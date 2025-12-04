-- init.sql: executed by Postgres image on first startup
-- Creates a sample table used by the face recognition app

CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    promo TEXT,
    image_path TEXT,
    last_seen TIMESTAMP DEFAULT NULL
);

-- Insert two sample rows corresponding to the images copied into the faceapp image
INSERT INTO people (name, promo, image_path) VALUES
  ('Mathis', '5IRC', '/faces/mathis.jpeg'),
  ('Clem', '4IRC', '/faces/clem.jpeg')
ON CONFLICT DO NOTHING;
