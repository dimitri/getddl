  select distinct n.nspname from pg_namespace n 
   where     n.nspname not like 'pg_temp%' 
         and n.nspname not like 'pg_toast%' 
	 and n.nspname not in ('pg_catalog',
	     	       	       'information_schema',
                               'pgq',
                               'londiste',
                               'utl_file',
                               'plvstr',
                               'plvchr',
                               'plvdate',
                               'plvsubst',
                               'plvlex',
                               'dbms_pipe',
                               'dbms_alert',
                               'dbms_output',
                               'dbms_utility',
                               'oracle',
                               'oracompat')
order by n.nspname;
