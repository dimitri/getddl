#!/usr/bin/env python
# -*- coding: utf-8 -*-
# libs for database interface

import os.path, string, subprocess, shlex, tempfile, sys
import psycopg2.psycopg1 as psycopg
from optparse import OptionParser

def maketree(path):
    if os.path.isdir(path) != 1 :
        os.makedirs(path)

class GetDdl:
	def __init__(self,options):
                self.options=options
                self.l_schemas=[]
                self.dbname = options.dbname
                maketree( self.dbname )

                self.dbconn = psycopg.connect('host=%s port=%s dbname=%s user=%s' % \
                                                      (self.options.dbhost,
                                                       self.options.dbport,
                                                       self.options.dbname,
                                                       self.options.dbuser))

                self.pg_opts= '-h %s -p %s -U %s %s' % (self.options.dbhost,
							self.options.dbport,
							self.options.dbuser,
							self.options.dbname)

                self.getVersion()
                self.list_nsp()

		if self.version == '8.3':
			self.cr83 = self.getsql("function.body.83")
		else:
			self.cr83 = ""

		if options.tables or options.views or options.all:
			# prepare the work
                        print "Dump schema and extract pg_restore listing :",
			self.pg_dump_schema()
			self.get_restore_list()
			print "OK"

                if options.tables or options.all:
                        print "Extract Tables :",

                        for schema in self.l_schemas:
                                self.extract_tables(schema)
                        print "OK"


                if options.sequences or options.all:
                        print "Extract Sequences :",
                        for schema in self.l_schemas:
                                self.extract_seq(schema)
                        print "OK"

                if options.views or options.all:
                        print "Extract Views :",
                        for schema in self.l_schemas:
                                self.extract_views(schema)
                        print "OK"

                if options.functions or options.all:
                        print "Extract Functions :",
                        for schema in self.l_schemas:
                                self.extract_functions(schema)
                        print "OK"

                if options.triggers or options.all:
                        print "Extract Triggers :",
                        for schema in self.l_schemas:
                                self.extract_triggers(schema)
                        print "OK"

	def pg_dump_schema(self):
		""" pg_dump -Fc -s dbname > dbname/schema.dump """
		cmd = shlex.split("pg_dump -Fc -s %s" % self.pg_opts)
		out = open(os.path.join(self.dbname, "schema.dump"), "wb+")
		proc = subprocess.Popen(cmd, stdout=out)
		o, e = proc.communicate()
		return

	def get_restore_list(self):
		""" pg_restore -l dbname/schema.dump > dbname/pg_restore.list """
		out = open(os.path.join(self.dbname, "pg_restore.list"), "wb+")
		dmp = os.path.join(self.dbname, "schema.dump")
		cmd = shlex.split("pg_restore -l %s" % dmp)
		proc = subprocess.Popen(cmd, stdout=out)
		o, e = proc.communicate()
		return

	def get_table_def(self, kind, schema, table, path):
		""" pg_restore -L $(grep 'TABLE.*table' dbname/pg_restore.list) > path/table.sql """
		c, f = tempfile.mkstemp()
		lst = os.path.join(self.dbname, "pg_restore.list")
		cmd = shlex.split("grep '%s.* %s %s ' %s" % (kind, schema, table, lst))
		proc = subprocess.Popen(cmd, stdout=c)
		o, e = proc.communicate()

		dmp = os.path.join(self.dbname, "schema.dump")
		out = open(os.path.join(path, "%s.sql" % table), "w+")
		cmd = shlex.split("pg_restore -L %s %s" %(f, dmp))
		proc = subprocess.Popen(cmd, stdout=out)
		o, e = proc.communicate()

		# don't forget to remove the temp files
		os.close(c)
		os.unlink(f)

		return

	def getsql(self, name, **kw):
		""" Get the SQL query template and substitute the mappings """
		q = string.Template( open(  os.path.dirname(__file__) + '/' + os.path.join('sql', '%s.sql' % name) ).read())
		return q.substitute(kw)

        def getVersion(self):
                cversion = self.dbconn.cursor()
                cversion.execute("select substring( version()::text ,'([789].[0123456789])'::text) ;")
                record = cversion.fetchall()
                for v in record:
                        self.version = v[0]

        def list_nsp(self):
		""" return the list of the schemas to consider """
                cnsp = self.dbconn.cursor()
                cnsp.execute(self.getsql("schemas"))
                record = cnsp.fetchall()
                for nsp in record:
                        self.l_schemas.append(nsp[0])
                return

        def extract_seq(self,schema):
                cseqs = self.dbconn.cursor()
                statement = self.getsql("schemas.list.seqs", schema=schema)
                cseqs.execute(statement)
                record = cseqs.fetchall()
                if len(record)>0:
                        path= os.path.join(self.dbname, self.options.sequencesdir, schema)
                        maketree(path)
                        createseq=self.dbconn.cursor()
                        for seq, in record:
                                createseq.execute(self.getsql('get.seq', schema=schema, seq=seq))
                                s = createseq.fetchone()
                                try:
                                        f = open(os.path.join(path, '%s.sql' % seq), 'w')
                                        f.write(s[0])
                                        f.close()
                                except IOError:
                                        pass

        def extract_tables(self, schema):
		# prepare the work
                ctables = self.dbconn.cursor()
                statement = self.getsql("schemas.list.tables", schema=schema)
                ctables.execute(statement)
                record = ctables.fetchall()
                if len(record)>0:
                        path = os.path.join(self.dbname, self.options.tablesdir, schema)
                        maketree( path )
                        for table, in record:
				self.get_table_def('TABLE', schema, table, path)

        def extract_views(self, schema):
                cviews = self.dbconn.cursor()
                statement = self.getsql("schemas.list.views", schema=schema)
                cviews.execute(statement)
                record = cviews.fetchall()
                if len(record)>0:
                        path = os.path.join(self.dbname, 'views', schema)
                        maketree(path)
                        for view, in record:
				self.get_table_def('VIEW', schema, view, path)

        def extract_functions(self, schema, trigger="NOT"):
                cfuncs = self.dbconn.cursor()
                statement = self.getsql("schemas.list.functions", schema=schema, trigger_not=trigger)
                cfuncs.execute(statement)
                record = cfuncs.fetchall()
                if len(record)>0:
			if trigger == "NOT":
				path= os.path.join(self.dbname, self.options.functionsdir, schema)
			else:
				path= os.path.join(self.dbname, self.options.triggersdir, schema)
                        maketree(path)
                        funbody=self.dbconn.cursor()
                        for func, in record:
				q = self.getsql('function.body',
						schema=schema, proname=func,
						trigger_not=trigger, costrows83=self.cr83)
                                funbody.execute(q)
                                fbody = funbody.fetchone()
				if not fbody:
					print func
					sys.exit(0)
                                try:
                                        f = open(os.path.join(path, '%s.sql' % func), 'a')
                                        f.write(fbody[0])
                                        f.close()
                                except IOError:
                                        pass

        def extract_triggers(self, schema):
		return self.extract_functions(schema, trigger = "")

def main():
        parser = OptionParser()

        parser.add_option("-c", "--config", dest = "config",
                          default = "pgloader.conf",
                          help    = "configuration file, defauts to pgloader.conf")

        parser.add_option("-a", "--all",
                          action="store_true", dest="all",
                          default=False, help="-rvsft")

        parser.add_option("-r", "--tables",
                          action="store_true", dest="tables",
                          default=False, help="Extract Tables")

        parser.add_option("-v", "--views",
                          action="store_true", dest="views",
                          default=False, help="Extract Views")

        parser.add_option("-s", "--sequences",
                          action="store_true", dest="sequences",
                          default=False, help="Extract Sequences")

        parser.add_option("-f", "--functions",
                          action="store_true", dest="functions",
                          default=False, help="Extract Functions")

        parser.add_option("-t", "--triggers",
                          action="store_true", dest="triggers",
                          default=False, help="Extract Triggers")

        parser.add_option("-R", "--tables-dir",
                          dest="tablesdir", default="tables",
                          help="Tables dir")

        parser.add_option("-V", "--views-dir",
                          dest="viewsdir", default="views",
                          help="Views dir")

        parser.add_option("-S", "--sequences-dir",
                          dest="sequencesdir", default="sequences",
                          help="Sequences dir")

        parser.add_option("-F", "--functions-dir",
                          dest="functionsdir", default="functions",
                          help="Functions dir")

        parser.add_option("-T", "--triggers-dir",
                          dest="triggersdir", default="triggers",
                          help="Triggers dir")

        parser.add_option("-d", "--database",
                          help="Database to extract (mandatory)", metavar="DB",
                          dest="dbname")

        parser.add_option("-H", "--host",
                          help="hostname", default="localhost",
                          metavar="HOST", dest="dbhost")

        parser.add_option("-p", "--port",
                          help="TCP Port", default="5432",
                          metavar="HOST", dest="dbport")

        parser.add_option("-U", "--username",
                          help="DB User Name", default="postgres",
                          metavar="USERNAME", dest="dbuser")

        (options, args) = parser.parse_args()

        if options.dbname is not None and len(options.dbname)>0 :
                getddl = GetDdl( options )
        else:
                print "Options -d is mandatory."
                parser.print_help()

if __name__ == '__main__':
     main()
