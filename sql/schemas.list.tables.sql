  select c.relname
    from pg_catalog.pg_class c join pg_namespace n on c.relnamespace=n.oid 
   where c.relkind='r' and n.nspname='${schema}'
order by c.relname 