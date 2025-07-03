"""
SQLite database models for persistent conversation storage
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseManager:
    """Manages SQLite database for conversation persistence"""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path
        self._connection = None
        
        # For file-based databases, ensure directory exists
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # For in-memory databases, we need to maintain a persistent connection
        if db_path == ":memory:":
            self._connection = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute('PRAGMA journal_mode=WAL')
            # Enable foreign key constraints
            self._connection.execute('PRAGMA foreign_keys=ON')
        
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        if self._connection:
            # Use persistent connection for in-memory database
            conn = self._connection
            conn.executescript('''
                -- Users table for authentication
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    picture TEXT,
                    verified_email BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL,
                    last_login TIMESTAMP
                );
                
                -- Chat sessions table
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                );
                
                -- Messages table
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT, -- JSON string for additional data
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                );
                
                -- Session memory/context table
                CREATE TABLE IF NOT EXISTS session_memory (
                    session_id TEXT PRIMARY KEY,
                    context_state TEXT NOT NULL, -- JSON string of the context state
                    history TEXT NOT NULL, -- JSON string of the history
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                );
                
                -- Indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp);
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON chat_sessions (updated_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
            ''')
            
            # Add user_id column to existing chat_sessions table if it doesn't exist
            try:
                conn.execute('ALTER TABLE chat_sessions ADD COLUMN user_id TEXT DEFAULT "anonymous_user"')
                conn.commit()
                print("✅ Added user_id column to existing chat_sessions table")
            except sqlite3.OperationalError as e:
                # Column already exists or other error
                if "duplicate column name" in str(e).lower():
                    print("✅ user_id column already exists")
                else:
                    print(f"⚠️ Database migration issue: {e}")
                pass
        else:
            # Use temporary connection for file-based database
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute('PRAGMA foreign_keys=ON')
                conn.executescript('''
                    -- Users table for authentication
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        picture TEXT,
                        verified_email BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL,
                        last_login TIMESTAMP
                    );
                    
                    -- Chat sessions table
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    );
                    
                    -- Messages table
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        timestamp TIMESTAMP NOT NULL,
                        metadata TEXT, -- JSON string for additional data
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                    );
                    
                    -- Session memory/context table
                    CREATE TABLE IF NOT EXISTS session_memory (
                        session_id TEXT PRIMARY KEY,
                        context_state TEXT NOT NULL, -- JSON string of the context state
                        history TEXT NOT NULL, -- JSON string of the history
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                    );
                    
                    -- Indexes for better performance
                    CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id);
                    CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp);
                    CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON chat_sessions (updated_at);
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON chat_sessions (user_id);
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
                ''')
                
                # Add user_id column to existing chat_sessions table if it doesn't exist
                try:
                    conn.execute('ALTER TABLE chat_sessions ADD COLUMN user_id TEXT DEFAULT "anonymous_user"')
                    conn.commit()
                    print("✅ Added user_id column to existing chat_sessions table")
                except sqlite3.OperationalError as e:
                    # Column already exists or other error
                    if "duplicate column name" in str(e).lower():
                        print("✅ user_id column already exists")
                    else:
                        print(f"⚠️ Database migration issue: {e}")
                    pass
    
    def get_connection(self):
        """Get database connection with row factory"""
        if self._connection:
            # Return persistent connection for in-memory database
            return self._connection
        else:
            # Create new connection for file-based database
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            # Enable foreign key constraints
            conn.execute('PRAGMA foreign_keys=ON')
            return conn
    
    # User operations
    def create_or_update_user(self, user_id: str, email: str, name: str, 
                             picture: Optional[str] = None, verified_email: bool = False) -> Dict[str, Any]:
        """Create or update a user"""
        now = datetime.now()
        
        if self._connection:
            conn = self._connection
            # Try to update existing user first
            cursor = conn.execute('''
                UPDATE users SET name = ?, picture = ?, verified_email = ?, last_login = ?
                WHERE id = ?
            ''', (name, picture, verified_email, now, user_id))
            
            if cursor.rowcount == 0:
                # User doesn't exist, create new one
                conn.execute('''
                    INSERT INTO users (id, email, name, picture, verified_email, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, email, name, picture, verified_email, now, now))
            
            conn.commit()
        else:
            with self.get_connection() as conn:
                # Try to update existing user first
                cursor = conn.execute('''
                    UPDATE users SET name = ?, picture = ?, verified_email = ?, last_login = ?
                    WHERE id = ?
                ''', (name, picture, verified_email, now, user_id))
                
                if cursor.rowcount == 0:
                    # User doesn't exist, create new one
                    conn.execute('''
                        INSERT INTO users (id, email, name, picture, verified_email, created_at, last_login)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, email, name, picture, verified_email, now, now))
        
        return {
            'id': user_id,
            'email': email,
            'name': name,
            'picture': picture,
            'verified_email': verified_email,
            'last_login': now
        }
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM users WHERE id = ?
            ''', (user_id,)).fetchone()
            
            if row:
                return dict(row)
        return None
    
    # Session operations
    def create_session(self, session_id: str, user_id: str, title: str) -> Dict[str, Any]:
        """Create a new chat session"""
        now = datetime.now()
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            conn.execute('''
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, title, now, now))
            
            # Initialize empty memory for the session
            conn.execute('''
                INSERT INTO session_memory (session_id, context_state, history, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (session_id, '{}', '[]', now))
            conn.commit()
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, user_id, title, now, now))
                
                # Initialize empty memory for the session
                conn.execute('''
                    INSERT INTO session_memory (session_id, context_state, history, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, '{}', '[]', now))
        
        return {
            'id': session_id,
            'user_id': user_id,
            'title': title,
            'created_at': now,
            'updated_at': now
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM chat_sessions WHERE id = ?
            ''', (session_id,)).fetchone()
            
            if row:
                return dict(row)
        return None
    
    def update_session(self, session_id: str):
        """Update session timestamp"""
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            conn.execute('''
                UPDATE chat_sessions SET updated_at = ? WHERE id = ?
            ''', (datetime.now(), session_id))
            conn.commit()
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE chat_sessions SET updated_at = ? WHERE id = ?
                ''', (datetime.now(), session_id))
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List sessions ordered by most recent, optionally filtered by user"""
        with self.get_connection() as conn:
            # Check if messages table exists
            table_exists = conn.execute('''
                SELECT name FROM sqlite_master WHERE type='table' AND name='messages'
            ''').fetchone()
            
            if table_exists:
                # Use JOIN query with message count
                if user_id:
                    rows = conn.execute('''
                        SELECT cs.*, COUNT(m.id) as message_count
                        FROM chat_sessions cs
                        LEFT JOIN messages m ON cs.id = m.session_id
                        WHERE cs.user_id = ?
                        GROUP BY cs.id
                        ORDER BY cs.updated_at DESC
                    ''', (user_id,)).fetchall()
                else:
                    rows = conn.execute('''
                        SELECT cs.*, COUNT(m.id) as message_count
                        FROM chat_sessions cs
                        LEFT JOIN messages m ON cs.id = m.session_id
                        GROUP BY cs.id
                        ORDER BY cs.updated_at DESC
                    ''').fetchall()
            else:
                # Fallback to simple query without message count
                if user_id:
                    rows = conn.execute('''
                        SELECT *, 0 as message_count FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC
                    ''', (user_id,)).fetchall()
                else:
                    rows = conn.execute('''
                        SELECT *, 0 as message_count FROM chat_sessions ORDER BY updated_at DESC
                    ''').fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and all related data"""
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            cursor = conn.execute('''
                DELETE FROM chat_sessions WHERE id = ?
            ''', (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    DELETE FROM chat_sessions WHERE id = ?
                ''', (session_id,))
                return cursor.rowcount > 0
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            cursor = conn.execute('''
                UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?
            ''', (title, datetime.now(), session_id))
            conn.commit()
            return cursor.rowcount > 0
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?
                ''', (title, datetime.now(), session_id))
                return cursor.rowcount > 0
    
    # Message operations
    def add_message(self, message_id: str, session_id: str, content: str, 
                   role: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a message to a session"""
        now = datetime.now()
        metadata_json = json.dumps(metadata) if metadata else None
        
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            conn.execute('''
                INSERT INTO messages (id, session_id, content, role, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (message_id, session_id, content, role, now, metadata_json))
            conn.commit()
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO messages (id, session_id, content, role, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (message_id, session_id, content, role, now, metadata_json))
        
        # Update session timestamp
        self.update_session(session_id)
        
        return {
            'id': message_id,
            'session_id': session_id,
            'content': content,
            'role': role,
            'timestamp': now,
            'metadata': metadata
        }
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp
            ''', (session_id,)).fetchall()
            
            messages = []
            for row in rows:
                message = dict(row)
                # Parse metadata JSON
                if message['metadata']:
                    message['metadata'] = json.loads(message['metadata'])
                messages.append(message)
            
            return messages
    
    # Memory operations
    def save_session_memory(self, session_id: str, context_state: Dict[str, Any], 
                           history: List[Dict[str, Any]]):
        """Save session memory (context state and history)"""
        if self._connection:
            # For persistent connection, handle transaction manually
            conn = self._connection
            conn.execute('''
                INSERT OR REPLACE INTO session_memory 
                (session_id, context_state, history, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (session_id, json.dumps(context_state), json.dumps(history), datetime.now()))
            conn.commit()
        else:
            # For file-based database, use context manager
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO session_memory 
                    (session_id, context_state, history, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, json.dumps(context_state), json.dumps(history), datetime.now()))
    
    def get_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session memory"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM session_memory WHERE session_id = ?
            ''', (session_id,)).fetchone()
            
            if row:
                return {
                    'session_id': row['session_id'],
                    'context_state': json.loads(row['context_state']),
                    'history': json.loads(row['history']),
                    'updated_at': row['updated_at']
                }
        return None
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up sessions older than specified days"""
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM chat_sessions 
                WHERE datetime(updated_at) < datetime(?, 'unixepoch')
            ''', (cutoff_date,))
            
            return cursor.rowcount
    
    def close(self):
        """Close the database connection if it exists"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global database manager instance
db_manager = DatabaseManager()