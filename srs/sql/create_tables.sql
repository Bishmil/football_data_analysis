-- Leagues

CREATE TABLE leagues (
    league_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL
);


-- Seasons

CREATE TABLE seasons (
    season_id BIGINT PRIMARY KEY,
    league_id BIGINT NOT NULL,
    name TEXT NOT NULL,

    CONSTRAINT fk_seasons_league
        FOREIGN KEY (league_id)
        REFERENCES leagues (league_id),

    CONSTRAINT uq_seasons_league_name
        UNIQUE (league_id, name)
);


-- Teams

CREATE TABLE teams (
    team_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    short_code VARCHAR(10)
);


-- Players

CREATE TABLE players (
    player_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth DATE,
    height INTEGER,
    weight NUMERIC(6,2),
    nationality TEXT,

    CONSTRAINT chk_players_height
        CHECK (height IS NULL OR height > 0),

    CONSTRAINT chk_players_weight
        CHECK (weight IS NULL OR weight > 0)
);


-- Positions
-- Sportmonks position_id:
-- 24 = Goalkeeper
-- 25 = Defender
-- 26 = Midfielder
-- 27 = Attacker

CREATE TABLE positions (
    position_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE
);

INSERT INTO positions (
    position_id,
    name,
    code
)
VALUES
    (24, 'Goalkeeper', 'GK'),
    (25, 'Defender', 'DEF'),
    (26, 'Midfielder', 'MID'),
    (27, 'Attacker', 'ATT');


-- Matches

CREATE TABLE matches (
    match_id BIGINT PRIMARY KEY,
    home_team_id BIGINT NOT NULL,
    away_team_id BIGINT NOT NULL,
    starting_at TIMESTAMPTZ NOT NULL,
    season_id BIGINT NOT NULL,
    round_id BIGINT,
    venue_id BIGINT,
    state_id BIGINT,
    result_info TEXT,

    CONSTRAINT fk_matches_home_team
        FOREIGN KEY (home_team_id)
        REFERENCES teams (team_id),

    CONSTRAINT fk_matches_away_team
        FOREIGN KEY (away_team_id)
        REFERENCES teams (team_id),

    CONSTRAINT fk_matches_season
        FOREIGN KEY (season_id)
        REFERENCES seasons (season_id),

    CONSTRAINT chk_matches_different_teams
        CHECK (home_team_id <> away_team_id)
);


-- Team match statistics

CREATE TABLE team_match (
    match_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    corners INTEGER,
    ball_possession NUMERIC(5,2),
    goals INTEGER,
    assists INTEGER,
    successful_dribbles_percentage NUMERIC(5,2),
    yellowcards INTEGER,
    redcards INTEGER,

    CONSTRAINT pk_team_match
        PRIMARY KEY (match_id, team_id),

    CONSTRAINT fk_team_match_match
        FOREIGN KEY (match_id)
        REFERENCES matches (match_id),

    CONSTRAINT fk_team_match_team
        FOREIGN KEY (team_id)
        REFERENCES teams (team_id),

    CONSTRAINT chk_team_match_ball_possession
        CHECK (
            ball_possession IS NULL
            OR ball_possession BETWEEN 0 AND 100
        ),

    CONSTRAINT chk_team_match_dribbles_percentage
        CHECK (
            successful_dribbles_percentage IS NULL
            OR successful_dribbles_percentage BETWEEN 0 AND 100
        )
);


-- Player match statistics

CREATE TABLE player_match (
    player_id BIGINT NOT NULL,
    match_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL,
    position_id BIGINT,

    minutes_played INTEGER,
    rating NUMERIC(4,2),
    touches INTEGER,
    possession_lost INTEGER,

    goals INTEGER,
    assists INTEGER,
    shots_total INTEGER,
    shots_on_target INTEGER,
    shots_off_target INTEGER,
    big_chances_created INTEGER,
    big_chances_missed INTEGER,
    key_passes INTEGER,
    chances_created INTEGER,
    dribble_attempts INTEGER,
    successful_dribbles INTEGER,
    dribbled_past INTEGER,
    total_crosses INTEGER,
    accurate_crosses INTEGER,
    through_balls INTEGER,
    through_balls_won INTEGER,
    offsides INTEGER,

    passes INTEGER,
    accurate_passes INTEGER,
    long_balls INTEGER,
    long_balls_won INTEGER,
    passes_in_final_third INTEGER,
    backward_passes INTEGER,

    tackles INTEGER,
    tackles_won INTEGER,
    interceptions INTEGER,
    clearances INTEGER,
    total_duels INTEGER,
    duels_won INTEGER,
    duels_lost INTEGER,
    aerials INTEGER,
    aerials_won INTEGER,
    aerials_lost INTEGER,
    ball_recovery INTEGER,
    dispossessed INTEGER,

    fouls INTEGER,
    fouls_drawn INTEGER,
    yellowcards INTEGER,
    redcards INTEGER,

    saves INTEGER,
    saves_insidebox INTEGER,
    punches INTEGER,
    good_high_claim INTEGER,
    goalkeeper_goals_conceded INTEGER,

    penalties_scored INTEGER,
    penalties_missed INTEGER,
    penalties_won INTEGER,
    penalties_committed INTEGER,
    penalties_saved INTEGER,

    CONSTRAINT pk_player_match
        PRIMARY KEY (player_id, match_id),

    CONSTRAINT fk_player_match_player
        FOREIGN KEY (player_id)
        REFERENCES players (player_id),

    CONSTRAINT fk_player_match_match
        FOREIGN KEY (match_id)
        REFERENCES matches (match_id),

    CONSTRAINT fk_player_match_team
        FOREIGN KEY (team_id)
        REFERENCES teams (team_id),

    CONSTRAINT fk_player_match_position
        FOREIGN KEY (position_id)
        REFERENCES positions (position_id)
);