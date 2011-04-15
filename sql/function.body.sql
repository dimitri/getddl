SELECT E'-- \n-- '||p.proname||E'\n-- \ncreate or replace function '||n.nspname||'.'||p.proname||E'\n(\n\t'||
        coalesce(CASE WHEN proallargtypes IS NOT NULL 
                THEN 
                pg_catalog.array_to_string(ARRAY( SELECT CASE WHEN p.proargmodes[s.i] = 'i' THEN '' 
                                                              WHEN p.proargmodes[s.i] = 'o' THEN 'OUT '
                                                              WHEN p.proargmodes[s.i] = 'b' THEN 'INOUT '
                                                          END ||
                                                         CASE WHEN COALESCE(p.proargnames[s.i], '') = '' 
                                                              THEN ''
                                                              ELSE p.proargnames[s.i] || ' ' 
                                                          END || pg_catalog.format_type(p.proallargtypes[s.i], NULL)
                                                   FROM pg_catalog.generate_series(1, pg_catalog.array_upper(p.proallargtypes, 1)) AS s(i) ), E',\n\t')
                ELSE
                pg_catalog.array_to_string(ARRAY( SELECT CASE WHEN COALESCE(p.proargnames[s.i+1], '') = '' THEN ''
                                                              ELSE p.proargnames[s.i+1] || ' ' 
                                                          END 
                                                          || pg_catalog.format_type(p.proargtypes[s.i], NULL)
                                                   FROM pg_catalog.generate_series(0, pg_catalog.array_upper(p.proargtypes, 1)) AS s(i) ), E',\n\t')
                END,'') 
        || E'\n)\nreturns '
        || (select case when p.proretset='t'::boolean then ' SETOF ' else '' end ) 
        || pg_catalog.format_type(p.prorettype,NULL)
        || (select case when encode( p.probin::bytea , 'escape') <> '-' then E' as \''||encode( p.probin::bytea, 'escape')||E'\', \''||p.prosrc||E'\' \n' 
                        else E'\nas $$BODY$$\n' || p.prosrc || E'\n$$BODY$$\n' end)
        || ( select case when p.provolatile='v' then ' VOLATILE '
                when p.provolatile='s' then ' STABLE ' 
                when p.provolatile='i' then ' IMMUTABLE ' 
                else '' end ) || E'\n' 
        || ( select case when p.prosecdef='t' then ' SECURITY DEFINER '
                when p.prosecdef='f' then ' SECURITY INVOKER ' 
                else '' end ) || E'\n' 
        || ( select case when p.proisstrict='t' then ' STRICT '
                when p.proisstrict='f' then ' CALLED ON NULL INPUT ' 
                else '' end ) || E'\n' 
        || ' LANGUAGE ' || (select l.lanname from pg_catalog.pg_language l where l.oid=p.prolang) || E'\n'
        ${costrows83}
        || '\n;\n
    FROM pg_catalog.pg_proc p 
         LEFT JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
   WHERE p.prorettype <> 'pg_catalog.cstring'::pg_catalog.regtype 
         AND (p.proargtypes[0] IS NULL OR   p.proargtypes[0] <> 'pg_catalog.cstring'::pg_catalog.regtype)
         AND NOT p.proisagg and n.nspname = '${schema}' and p.proname='${proname}'
         AND pg_catalog.format_type(p.prorettype,NULL) ${trigger_not} IN ('trigger', '"trigger"')
ORDER BY array_upper(p.proargnames,1) desc 
