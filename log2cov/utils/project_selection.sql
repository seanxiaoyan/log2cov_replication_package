
--  get python repos with num commits
WITH python_repo AS (
    WITH
        repositories AS (
        SELECT
        t2.repo_name,
        t2.LANGUAGE
        FROM (
        SELECT
            repo_name,
            LANGUAGE,
            RANK() OVER (PARTITION BY t1.repo_name ORDER BY t1.language_bytes DESC) AS rank
        FROM (
            SELECT
            repo_name,
            arr.name AS LANGUAGE,
            arr.bytes AS language_bytes
            FROM
            `bigquery-public-data.github_repos.languages`,
            UNNEST(LANGUAGE) arr ) AS t1 ) AS t2
        WHERE
        rank = 1)
    SELECT
        repo_name,
        LANGUAGE
    FROM
        repositories
    WHERE
        LANGUAGE = 'Python'
        )
SELECT COUNT(commit) AS num_commits, Rname FROM `bigquery-public-data.github_repos.commits`
LEFT JOIN UNNEST(`bigquery-public-data.github_repos.commits`.repo_name) Rname
INNER JOIN python_repo ON python_repo.repo_name = Rname
GROUP BY Rname
ORDER BY num_commits DESC

-- get python repos with ordered num files

WITH python_repo AS (
    WITH
        repositories AS (
        SELECT
        t2.repo_name,
        t2.LANGUAGE
        FROM (
        SELECT
            repo_name,
            LANGUAGE,
            RANK() OVER (PARTITION BY t1.repo_name ORDER BY t1.language_bytes DESC) AS rank
        FROM (
            SELECT
            repo_name,
            arr.name AS LANGUAGE,
            arr.bytes AS language_bytes
            FROM
            `bigquery-public-data.github_repos.languages`,
            UNNEST(LANGUAGE) arr ) AS t1 ) AS t2
        WHERE
        rank = 1)
    SELECT
        repo_name,
        LANGUAGE
    FROM
        repositories
    WHERE
        LANGUAGE = 'Python'
        )
    SELECT COUNT(path) AS num_files, `bigquery-public-data.github_repos.files`.repo_name AS Rname FROM `bigquery-public-data.github_repos.files`
    INNER JOIN python_repo ON python_repo.repo_name = `bigquery-public-data.github_repos.files`.repo_name
    GROUP BY Rname




-- merge two tables with inner join
SELECT 
 l.Rname, num_files, num_commits
  FROM `python_repo.num_files_python_repo` l
   INNER JOIN `python_repo.repo_commits_ordered` r
    ON l.Rname = r.Rname
WHERE l.Rname IN (
    SELECT Rname
    FROM `python_repo.forked_repo`
)


SELECT 
 Rname, num_files, num_commits, RANK() OVER (ORDER BY (commit_rank + file_rank) ASC) AS overall_rank, commit_rank, file_rank
 FROM `python_repo.repo_rank_commit_file`
ORDER BY overall_rank ASC

-- RANK REPO
WITH seperate_rank AS (SELECT 
 Rname, num_files, RANK() OVER (ORDER BY num_commits DESC) AS commit_rank, num_commits, RANK() OVER (ORDER BY num_files DESC) AS file_rank
 FROM `python_repo.repo_numfile_numcommit`)

SELECT 
 Rname, num_files, num_commits, RANK() OVER (ORDER BY (commit_rank + file_rank) ASC) AS overall_rank, commit_rank, file_rank
 FROM seperate_rank
ORDER BY overall_rank ASC