CREATE VIEW player_match_analysis AS
SELECT
    m.match_id,
    m.season_id,
    m.starting_at,

    p_m.player_id,
    p.name AS player_name,

    p_m.team_id,
    team_t.name AS team_name,

    CASE
        WHEN p_m.team_id != m.home_team_id THEN 'away'
        ELSE 'home'
    END AS home_away,

    opponent_tm.team_id AS opponent_id,
    opponent_t.name AS opponent_team_name,

    COALESCE(team_tm.goals, 0) AS team_goals,
    COALESCE(opponent_tm.goals, 0) AS opponent_goals,

    CASE
        WHEN COALESCE(team_tm.goals, 0) > COALESCE(opponent_tm.goals, 0)
            THEN 'win'
        WHEN COALESCE(team_tm.goals, 0) = COALESCE(opponent_tm.goals, 0)
            THEN 'draw'
        ELSE 'lose'
    END AS result,

    CASE
        WHEN COALESCE(team_tm.goals, 0) > COALESCE(opponent_tm.goals, 0)
            THEN 3
        WHEN COALESCE(team_tm.goals, 0) = COALESCE(opponent_tm.goals, 0)
            THEN 1
        ELSE 0
    END AS points,

    p_m.position_id,
    pos.name AS position_name,
    pos.code AS position_code,

    p_m.minutes_played,
    p_m.rating,
    p_m.touches,
    p_m.possession_lost,

    p_m.goals,
    p_m.assists,
    p_m.shots_total,
    p_m.shots_on_target,
    p_m.shots_off_target,
    p_m.big_chances_created,
    p_m.big_chances_missed,
    p_m.key_passes,
    p_m.chances_created,
    p_m.dribble_attempts,
    p_m.successful_dribbles,
    p_m.dribbled_past,
    p_m.total_crosses,
    p_m.accurate_crosses,
    p_m.through_balls,
    p_m.offsides,

    p_m.passes,
    p_m.accurate_passes,
    p_m.long_balls,
    p_m.long_balls_won,
    p_m.passes_in_final_third,
    p_m.backward_passes,

    p_m.tackles,
    p_m.tackles_won,
    p_m.interceptions,
    p_m.clearances,
    p_m.total_duels,
    p_m.duels_won,
    p_m.duels_lost,
    p_m.aerials,
    p_m.aerials_won,
    p_m.aerials_lost,
    p_m.ball_recovery,
    p_m.dispossessed,

    p_m.fouls,
    p_m.fouls_drawn,
    p_m.yellowcards,
    p_m.redcards,

    p_m.saves,
    p_m.saves_insidebox,
    p_m.punches,
    p_m.good_high_claim,
    p_m.goalkeeper_goals_conceded,

    p_m.penalties_scored,
    p_m.penalties_missed,
    p_m.penalties_won,
    p_m.penalties_committed,
    p_m.penalties_saved

FROM player_match AS p_m

JOIN matches AS m
    ON m.match_id = p_m.match_id

JOIN players AS p
    ON p.player_id = p_m.player_id

JOIN teams AS team_t
    ON team_t.team_id = p_m.team_id

JOIN positions AS pos
    ON pos.position_id = p_m.position_id

JOIN team_match AS team_tm
    ON team_tm.match_id = p_m.match_id
    AND team_tm.team_id = p_m.team_id

JOIN team_match AS opponent_tm
    ON opponent_tm.match_id = p_m.match_id
    AND opponent_tm.team_id != p_m.team_id

JOIN teams AS opponent_t
    ON opponent_t.team_id = opponent_tm.team_id

ORDER BY
    m.match_id,
    p_m.team_id,
    p_m.player_id;