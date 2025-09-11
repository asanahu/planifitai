PS E:\Variedades\PlanifitAI> docker-compose exec web alembic upgrade head
time="2025-09-11T07:12:29+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
time="2025-09-11T07:12:29+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.  
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> aac2998e7984, create users table
INFO  [alembic.runtime.migration] Running upgrade aac2998e7984 -> 9627e73a14f6, add users table  
INFO  [alembic.runtime.migration] Running upgrade 9627e73a14f6 -> c5379909c095, create users table (real)
INFO  [alembic.runtime.migration] Running upgrade c5379909c095 -> 796df29988e1, create_user_profiles_table
INFO  [alembic.runtime.migration] Running upgrade 796df29988e1 -> b234998e2f1b, create progress_entries
INFO  [alembic.runtime.migration] Running upgrade b234998e2f1b -> d1a5f8bda1a6, create nutrition 
tables
INFO  [alembic.runtime.migration] Running upgrade b234998e2f1b -> 7f4dbf4a3e20, Create routines, 
routine_days, exercise_catalog, and routine_exercises tables
INFO  [alembic.runtime.migration] Running upgrade 7f4dbf4a3e20 -> 123456789abc, add workout metric
ge routines+nutrition heads
INFO  [alembic.runtime.migration] Running upgrade 9742803658eb -> 9c1d2e8fa5c5, create notifications tables
INFO  [alembic.runtime.migration] Running upgrade 9c1d2e8fa5c5 -> e1a1c2d3e4f5, add content embeddings table
INFO  [alembic.runtime.migration] Running upgrade e1a1c2d3e4f5 -> 2025_09_08_0002, create foods table for nutrition cache
INFO  [alembic.runtime.migration] Running upgrade e1a1c2d3e4f5 -> f1b6f3a4c8d7, encrypt PHI columns
INFO  [alembic.runtime.migration] Running upgrade f1b6f3a4c8d7 -> b8d9e0f1a2c3, add fk indexes   
INFO  [alembic.runtime.migration] Running upgrade b8d9e0f1a2c3 -> add_profile_completed_0001, add profile_completed and align enums
INFO  [alembic.runtime.migration] Running upgrade add_profile_completed_0001, 2025_09_08_0002 -> 
0bebe059a9b5, merge profile_completed + foods heads
INFO  [alembic.runtime.migration] Running upgrade 0bebe059a9b5, 7f4dbf4a3e20 -> 2025_09_10_0003, 
add exercise meta columns and seed small catalog
INFO  [alembic.runtime.migration] Running upgrade 2025_09_10_0003 -> 2025_09_10_0004, Create routines tables if missing (compat fix)
INFO  [alembic.runtime.migration] Running upgrade 2025_09_10_0004 -> 2025_09_10_0005, expand progressmetric enum with workout and nutrition metrics
INFO  [alembic.runtime.migration] Running upgrade 2025_09_10_0005 -> 2025_09_10_0006, create routine_exercise_completions table
INFO  [alembic.runtime.migration] Running upgrade 2025_09_10_0006 -> 2025_09_10_0007, add equipment column to routine_days
PS E:\Variedades\PlanifitAI> docker-compose exec web python scripts/import_free_exercise_db.py --translate-es
time="2025-09-11T07:13:45+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
time="2025-09-11T07:13:45+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
Imported 873 exercises
PS E:\Variedades\PlanifitAI> docker-compose exec web alembic upgrade head
time="2025-09-11T07:13:57+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
time="2025-09-11T07:13:57+02:00" level=warning msg="The \"OPENROUTER_HTTP_REFERER\" variable is not set. Defaulting to a blank string."
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
PS E:\Variedades\PlanifitAI> 