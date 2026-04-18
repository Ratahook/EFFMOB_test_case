

async def bd_activate(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
        """)
        await conn.execute("""
                    CREATE TABLE IF NOT EXISTS roles (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL
                    )
                """)
        await conn.execute("""
                            CREATE TABLE IF NOT EXISTS user_roles (
                                user_id INT REFERENCES users(id) ON DELETE CASCADE,
                                role_id INT REFERENCES roles(id) ON DELETE CASCADE,
                                PRIMARY KEY (user_id, role_id)
                            )
                        """)
        await conn.execute("""
                            CREATE TABLE IF NOT EXISTS permissions (
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(100) UNIQUE NOT NULL
                            )
                        """)
        await conn.execute("""
                           CREATE TABLE IF NOT EXISTS role_permissions (
                                role_id INT REFERENCES roles(id) ON DELETE CASCADE,
                                permission_id INT REFERENCES permissions(id) ON DELETE CASCADE,
                                PRIMARY KEY (role_id, permission_id)
                            ) 
                        """)

async def set_testdata(pool):
     async with pool.acquire() as conn:
        await conn.execute("""
                                    INSERT INTO roles (name) VALUES ('admin'), ('user')
                                    ON CONFLICT DO NOTHING;
                                """)
        await conn.execute("""
                                   INSERT INTO permissions (name) VALUES 
                                    ('read_profile'),
                                    ('edit_profile'),
                                    ('delete_user')
                                    ON CONFLICT DO NOTHING;
                                """)
        await conn.execute("""
                                    INSERT INTO role_permissions (role_id, permission_id)
                                    SELECT r.id, p.id
                                    FROM roles r, permissions p
                                    WHERE r.name = 'admin'
                                    ON CONFLICT DO NOTHING;
                                """)
        await conn.execute("""
                                    INSERT INTO role_permissions (role_id, permission_id)
                                    SELECT r.id, p.id
                                    FROM roles r, permissions p
                                    WHERE r.name = 'user' AND p.name = 'read_profile'
                                    ON CONFLICT DO NOTHING;
                                """)