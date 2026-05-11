CREATE DATABASE IF NOT EXISTS Backtesting_Engine;
USE Backtesting_Engine;

-- ─────────────────────────────
-- 1. users
-- ─────────────────────────────
CREATE TABLE users (
    user_id       INT AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
);

-- ─────────────────────────────
-- 2. assets
-- ─────────────────────────────
CREATE TABLE assets (
    asset_id   INT AUTO_INCREMENT,
    symbol     VARCHAR(20)              NOT NULL UNIQUE,
    name       VARCHAR(100)             NOT NULL,
    asset_type ENUM('stock','crypto','forex') NOT NULL,
    created_at TIMESTAMP                DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_id)
);

-- ─────────────────────────────
-- 3. historical_prices
-- ─────────────────────────────
CREATE TABLE historical_prices (
    price_id   INT AUTO_INCREMENT,
    asset_id   INT             NOT NULL,
    open       DECIMAL(18,8)   NOT NULL,
    high       DECIMAL(18,8)   NOT NULL,
    low        DECIMAL(18,8)   NOT NULL,
    close      DECIMAL(18,8)   NOT NULL,
    volume     BIGINT          NOT NULL,
    timestamp  DATETIME        NOT NULL,
    PRIMARY KEY (price_id),
    UNIQUE  KEY uq_asset_time   (asset_id, timestamp),
    INDEX       idx_asset_time  (asset_id, timestamp),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- ─────────────────────────────
-- 4. strategies
-- ─────────────────────────────
CREATE TABLE strategies (
    strategy_id INT AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parameters  JSON,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (strategy_id)
);

-- ─────────────────────────────
-- 5. trades
-- ─────────────────────────────
CREATE TABLE trades (
    trade_id     INT AUTO_INCREMENT,
    user_id      INT                      NOT NULL,
    asset_id     INT                      NOT NULL,
    strategy_id  INT                      NOT NULL,
    trade_type   ENUM('BUY','SELL')        NOT NULL,
    quantity     DECIMAL(18,8)            NOT NULL,
    entry_price  DECIMAL(18,8)            NOT NULL,
    entry_time   DATETIME                 NOT NULL,
    exit_price   DECIMAL(18,8),
    exit_time    DATETIME,
    profit_loss  DECIMAL(18,8),
    status       ENUM('OPEN','CLOSED')    NOT NULL DEFAULT 'OPEN',
    created_at   TIMESTAMP                DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (trade_id),
    INDEX idx_trade_user     (user_id),
    INDEX idx_trade_asset    (asset_id),
    INDEX idx_trade_strategy (strategy_id),
    FOREIGN KEY (user_id)     REFERENCES users(user_id),
    FOREIGN KEY (asset_id)    REFERENCES assets(asset_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- ─────────────────────────────
-- 6. backtest_results
-- ─────────────────────────────
CREATE TABLE backtest_results (
    result_id       INT AUTO_INCREMENT,
    user_id         INT           NOT NULL,
    strategy_id     INT           NOT NULL,
    asset_id        INT           NOT NULL,
    date_from       DATE          NOT NULL,
    date_to         DATE          NOT NULL,
    initial_capital DECIMAL(18,2) NOT NULL,
    final_capital   DECIMAL(18,2),
    ran_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (result_id),
    INDEX idx_backtest_user     (user_id),
    INDEX idx_backtest_strategy (strategy_id),
    INDEX idx_backtest_asset    (asset_id),
    FOREIGN KEY (user_id)     REFERENCES users(user_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
    FOREIGN KEY (asset_id)    REFERENCES assets(asset_id)
);

-- ─────────────────────────────
-- 7. performance_metrics
-- ─────────────────────────────
CREATE TABLE performance_metrics (
    metric_id        INT AUTO_INCREMENT,
    result_id        INT           NOT NULL UNIQUE,
    win_rate         DECIMAL(5,2),
    total_pnl        DECIMAL(18,8),
    max_drawdown     DECIMAL(18,8),
    risk_reward_ratio DECIMAL(10,4),
    profit_factor    DECIMAL(10,4),
    total_trades     INT,
    winning_trades   INT,
    losing_trades    INT,
    PRIMARY KEY (metric_id),
    FOREIGN KEY (result_id) REFERENCES backtest_results(result_id)
);