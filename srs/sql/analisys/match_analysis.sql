CREATE VIEW match_analysis AS
SELECT
    m.match_id,
    m.season_id,
    m.round_id,
    m.starting_at,

    m.home_team_id,
    home_team.name AS home_team_name,

    m.away_team_id,
    away_team.name AS away_team_name,

    COALESCE(home_tm.goals, 0) AS home_goals,
    COALESCE(away_tm.goals, 0) AS away_goals,

    COALESCE(home_tm.goals, 0)
        - COALESCE(away_tm.goals, 0) AS goals_diff,

    CASE
        WHEN COALESCE(home_tm.goals, 0) > COALESCE(away_tm.goals, 0)
            THEN 'home_win'
        WHEN COALESCE(home_tm.goals, 0) = COALESCE(away_tm.goals, 0)
            THEN 'draw'
        ELSE 'away_win'
    END AS result,

    home_tm.corners AS home_corners,
    away_tm.corners AS away_corners,

    CASE
        WHEN home_tm.corners IS NOT NULL
         AND away_tm.corners IS NOT NULL
        THEN home_tm.corners - away_tm.corners
    END AS corners_diff,

    home_tm.ball_possession AS home_possession,
    away_tm.ball_possession AS away_possession,

    CASE
        WHEN home_tm.ball_possession IS NOT NULL
         AND away_tm.ball_possession IS NOT NULL
        THEN home_tm.ball_possession - away_tm.ball_possession
    END AS possession_diff,

    home_tm.successful_dribbles_percentage AS home_dribbles_pct,
    away_tm.successful_dribbles_percentage AS away_dribbles_pct,

    CASE
        WHEN home_tm.successful_dribbles_percentage IS NOT NULL
         AND away_tm.successful_dribbles_percentage IS NOT NULL
        THEN
            home_tm.successful_dribbles_percentage
            - away_tm.successful_dribbles_percentage
    END AS dribbles_diff,

    COALESCE(home_tm.yellowcards, 0) AS home_yellowcards,
    COALESCE(away_tm.yellowcards, 0) AS away_yellowcards,

    COALESCE(home_tm.redcards, 0) AS home_redcards,
    COALESCE(away_tm.redcards, 0) AS away_redcards

FROM matches AS m

JOIN teams AS home_team
    ON home_team.team_id = m.home_team_id

JOIN teams AS away_team
    ON away_team.team_id = m.away_team_id

LEFT JOIN team_match AS home_tm
    ON home_tm.match_id = m.match_id
    AND home_tm.team_id = m.home_team_id

LEFT JOIN team_match AS away_tm
    ON away_tm.match_id = m.match_id
    AND away_tm.team_id = m.away_team_id

ORDER BY
    m.starting_at,
    m.match_id;