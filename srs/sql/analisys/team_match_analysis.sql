CREATE VIEW team_match_analysis AS
SELECT
    m.match_id,
    m.season_id,
    m.round_id,
    m.starting_at,

    t_m.team_id,
    team_t.name AS team_name,

    CASE
        WHEN t_m.team_id != m.home_team_id THEN 'away'
        ELSE 'home'
    END AS home_away,

    opponent_tm.team_id AS opponent_id,
    opponent_t.name AS opponent_team_name,

    COALESCE(t_m.goals, 0) AS goals,
    COALESCE(opponent_tm.goals, 0) AS opponent_goals,

    COALESCE(t_m.goals, 0)
        - COALESCE(opponent_tm.goals, 0) AS goals_diff,

    CASE
        WHEN COALESCE(t_m.goals, 0) > COALESCE(opponent_tm.goals, 0)
            THEN 'win'
        WHEN COALESCE(t_m.goals, 0) = COALESCE(opponent_tm.goals, 0)
            THEN 'draw'
        ELSE 'lose'
    END AS result,

    CASE
        WHEN COALESCE(t_m.goals, 0) > COALESCE(opponent_tm.goals, 0)
            THEN 3
        WHEN COALESCE(t_m.goals, 0) = COALESCE(opponent_tm.goals, 0)
            THEN 1
        ELSE 0
    END AS points,

    t_m.corners,
    t_m.ball_possession,
    t_m.successful_dribbles_percentage,
    COALESCE(t_m.yellowcards, 0) AS yellowcards,
    COALESCE(t_m.redcards, 0) AS redcards

FROM team_match AS t_m

JOIN matches AS m
    ON m.match_id = t_m.match_id

JOIN team_match AS opponent_tm
    ON opponent_tm.match_id = t_m.match_id
    AND opponent_tm.team_id != t_m.team_id

JOIN teams AS team_t
    ON team_t.team_id = t_m.team_id

JOIN teams AS opponent_t
    ON opponent_t.team_id = opponent_tm.team_id

ORDER BY
    m.match_id,
    t_m.team_id;