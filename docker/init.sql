-- Create a replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replicator_password';

GRANT ALL PRIVILEGES ON DATABASE postgres TO replicator;

-- Allow replication and logical decoding
ALTER SYSTEM SET wal_level = logical;

SELECT pg_reload_conf();

create Schema bookies;
create Schema sims;
create Schema nasa;

-- Schema: bookies
CREATE TABLE bookies.bets (
    bet_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    odds DECIMAL(5, 2) NOT NULL,
    outcome VARCHAR(10) CHECK (outcome IN ('win', 'lose', 'pending')),
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookies.transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    bet_id INT REFERENCES bookies.bets(bet_id),
    amount DECIMAL(10, 2) NOT NULL,
    transaction_type VARCHAR(10) CHECK (transaction_type IN ('deposit', 'withdrawal')),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookies.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    balance DECIMAL(10, 2) DEFAULT 0.00
);


-- Schema: sims
CREATE TABLE sims.players (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT CHECK (age > 0),
    score INT DEFAULT 0
);

CREATE TABLE sims.games (
    game_id SERIAL PRIMARY KEY,
    game_name VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    release_date DATE
);

CREATE TABLE sims.sessions (
    session_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES sims.players(player_id),
    game_id INT REFERENCES sims.games(game_id),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP
);


-- Schema: nasa
CREATE TABLE nasa.missions (
    mission_id SERIAL PRIMARY KEY,
    mission_name VARCHAR(100) UNIQUE NOT NULL,
    launch_date DATE,
    status VARCHAR(50) CHECK (status IN ('planned', 'ongoing', 'completed'))
);

CREATE TABLE nasa.astronauts (
    astronaut_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    missions_participated INT DEFAULT 0
);

CREATE TABLE nasa.spacecrafts (
    spacecraft_id SERIAL PRIMARY KEY,
    spacecraft_name VARCHAR(100) UNIQUE NOT NULL,
    manufacturer VARCHAR(100),
    capacity INT CHECK (capacity > 0),
    mission_id INT REFERENCES nasa.missions(mission_id)
);