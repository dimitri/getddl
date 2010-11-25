 select E'-- \n-- '||c.relname||E'\n-- \ncreate sequence '|| c.relname 
        ||' increment by '||(select increment_by from ${schema}.${seq})
        ||' start with '||(select last_value from ${schema}.${seq}) || E'\n\t'
        ||(select case when min_value is null 
                       then ' no minvalue ' 
                       else 'minvalue '||min_value||' ' 
                  end 
            from ${schema}.${seq} 
          )
        ||(select case when max_value is null
                       then ' no maxvalue ' 
                       else 'maxvalue '||max_value||' ' 
                   end
            from ${schema}.${seq} 
          )
        ||(select 'cache '||cache_value from ${schema}.${seq} )
        ||(select case when is_cycled='f' 
                       then ' no ' 
                       else ' ' end 
            from ${schema}.${seq} 
          )
        || 'cycle'
        ||' owned by '
	||(select case when (select count(*)   
                               from pg_catalog.pg_class c1
                                     join pg_catalog.pg_depend d on c1.oid=d.objid 
                                     join pg_catalog.pg_namespace n1 on c1.relnamespace=n1.oid 
                              where c1.relkind='S' and d.refobjid in (select c2.oid from pg_catalog.pg_class c2 where c2.relkind='r'
                            ) 
                            and c1.relname='${seq}' and n1.nspname='${schema}')=1 
                       then (select (select n1.nspname||'.'||c1.relname 
                                       from pg_catalog.pg_class c1 
                                            join pg_namespace n1 on c1.relnamespace=n1.oid 
                                      where c1.oid=d.refobjid) 
                                    ||'.'||
                                    ( select a.attname
                                        from pg_catalog.pg_attribute a 
                                       where a.attrelid=d.refobjid and a.attnum=d.refobjsubid) 
                               from pg_catalog.pg_class c1
                                    join pg_catalog.pg_depend d on c1.oid=d.objid 
                                    join pg_catalog.pg_namespace n1 on c1.relnamespace=n1.oid 
                              where c1.relkind='S' 
                                    and d.refobjid in (select c2.oid from pg_catalog.pg_class c2 where c2.relkind='r') 
                                    and c1.relname='${seq}' and n1.nspname='${schema}'
                            )
                       else 'none ' 
                  end)
        ||E'; \n-- '
  from pg_catalog.pg_class c
       join pg_namespace n on c.relnamespace=n.oid 
 where c.relkind='S' and n.nspname='${schema}' and c.relname='${seq}'
