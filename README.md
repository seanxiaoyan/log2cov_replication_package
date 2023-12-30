Make sure you have docker (https://docs.docker.com/engine/install/) and docker-compose (https://docs.docker.com/compose/install/linux/) installed.

# Enviorment setup
On the root directory of the replication package,
Follow the steps below and execute the commands:
1. Set up containers 
docker-compose up -d

2. Go into the shell of log2cov container
docker exec -it log2cov /bin/bash

# Get data reported in the paper
1. In log2cov's shell, do
cd /
mongorestore --uri "mongodb://mongo:27017/" ./db_backup

<!-- If the previous command failed, run the following commands to load the databases separately -->

mongorestore --uri "mongodb://mongo:27017/" --db salt_unit_initial ./db_backup/salt_unit_initial
mongorestore --uri "mongodb://mongo:27017/" --db salt_unit_after ./db_backup/salt_unit_after
mongorestore --uri "mongodb://mongo:27017/" --db salt_integration ./db_backup/salt_integration
mongorestore --uri "mongodb://mongo:27017/" --db nova_unit_initial ./db_backup/nova_unit_initial
mongorestore --uri "mongodb://mongo:27017/" --db nova_unit_after ./db_backup/nova_unit_after
mongorestore --uri "mongodb://mongo:27017/" --db nova_functional ./db_backup/nova_functional
mongorestore --uri "mongodb://mongo:27017/" --db homeassistant_unit_initial ./db_backup/homeassistant_unit_initial
mongorestore --uri "mongodb://mongo:27017/" --db homeassistant_unit_after ./db_backup/homeassistant_unit_after
mongorestore --uri "mongodb://mongo:27017/" --db ground_truth ./db_backup/ground_truth



2. To get exploratory evaluation result. In log2cov's shell, do 
cd /log2cov
python3 exploratory_evaluation_result.py

3. To get RQ1 result. In log2cov's shell, do 
cd /log2cov
python3 rq1_result.py

4. To get RQ2 result. In log2cov's shell, do
cd /log2cov
python3 rq2_result.py

<!-- Note that the above scripts of getting results assume that you have all coverage databases in the mongodb -->

# Reprodoce the data of exploratory evaluation
1. cd /log2cov
<!-- Under main.py, uncomment the section of variable settings. Note that exploratory evaluation does not enable Remove Dependency-->
2. python3 main.py

<!-- You need to use the command mongodump to save the the coverage database, because another path of log2cov execution cleans up old data. The coverage database is named with the project's name -->

<!-- For example, a database called "salt" is what you get from log2cov for the salt system. If this is for unit test coverage without Remove Dependency, you can use mongodump and mongorestore to rename the database to "salt_unit_initial", as following commands: -->
mongodump --uri "mongodb://mongo:27017/" --db salt --out ./
mongorestore --uri "mongodb://mongo:27017/" --db salt_docker ./salt

# Reproduce RQ1 data
1. cd /log2cov
<!-- Under slice.py, uncomment the section of variable settings to select a subject system of experiment -->
<!-- under config.py, set "log_file_path" to the log file path of cooresponding subject system. -->
2. python3 slice.py

# Reproduce RQ2 data
<!-- Uncomment the section of variable settings, which is denoted as with Remove Dependency, for a subject system  -->
1. python3 main.py

