 || ( select case when p.procost <> 100 then ' cost ' || p.procost || E'\n' else '' end )
 || ( select case when p.prorows <> 0 then ' rows ' || p.prorows || E'\n' else '' end )
