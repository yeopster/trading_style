---
description: Show research status from the experiment registry
---
Run:
`python -c "import sqlite3;c=sqlite3.connect('experiments/registry.db');[print(r) for r in c.execute('select h.hypothesis_id,h.status,count(r.run_id),group_concat(r.verdict) from hypotheses h left join runs r using(hypothesis_id) group by 1')];print('total trials:',c.execute('select count(*) from runs').fetchone()[0])"`
Then summarise: hypotheses by status, total trials (this inflates the DSR hurdle), and the next action.
