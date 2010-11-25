  select distinct p.proname 
    from pg_proc p join pg_namespace n on p.pronamespace=n.oid 
         JOIN pg_catalog.pg_language l ON l.oid = p.prolang
   where n.nspname='${schema}' 
         and pg_catalog.format_type(p.prorettype,NULL) ${trigger_not} IN ('trigger', '"trigger"')
         and p.proisagg = 'f' 
	 AND l.lanname NOT IN ('internal', 'c')
order by p.proname ;