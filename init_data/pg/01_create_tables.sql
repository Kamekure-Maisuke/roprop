-- Create role enum type
DO $$ BEGIN
    CREATE TYPE employee_role AS ENUM ('user', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    profile_image BYTEA,
    role employee_role NOT NULL DEFAULT 'user',
    resignation_date DATE,
    transfer_date DATE
);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_resignation_date ON employees(resignation_date);
CREATE INDEX IF NOT EXISTS idx_employees_transfer_date ON employees(transfer_date);

-- Create pcs table
CREATE TABLE IF NOT EXISTS pcs (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    serial_number VARCHAR(255) NOT NULL UNIQUE,
    assigned_to UUID REFERENCES employees(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_pcs_assigned_to ON pcs(assigned_to);

-- Create pc_assignment_histories table
CREATE TABLE IF NOT EXISTS pc_assignment_histories (
    id UUID PRIMARY KEY,
    pc_id UUID NOT NULL REFERENCES pcs(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pc_assignment_histories_pc_id ON pc_assignment_histories(pc_id);
CREATE INDEX IF NOT EXISTS idx_pc_assignment_histories_employee_id ON pc_assignment_histories(employee_id);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY,
    sender_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_id ON chat_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(sender_id, receiver_id, created_at DESC);

-- Create blog_posts table
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY,
    author_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(created_at DESC);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Create blog_post_tags junction table
CREATE TABLE IF NOT EXISTS blog_post_tags (
    id UUID PRIMARY KEY,
    blog_post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(blog_post_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_blog_post_tags_blog_post_id ON blog_post_tags(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_blog_post_tags_tag_id ON blog_post_tags(tag_id);

-- Create blog_likes table
CREATE TABLE IF NOT EXISTS blog_likes (
    id UUID PRIMARY KEY,
    blog_post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blog_post_id, employee_id)
);
CREATE INDEX IF NOT EXISTS idx_blog_likes_blog_post_id ON blog_likes(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_blog_likes_employee_id ON blog_likes(employee_id);

-- Create meeting_rooms table
CREATE TABLE IF NOT EXISTS meeting_rooms (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0,
    location VARCHAR(255) NOT NULL,
    equipment TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_capacity ON meeting_rooms(capacity);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_location ON meeting_rooms(location);

-- Create meeting_room_reservations table
CREATE TABLE IF NOT EXISTS meeting_room_reservations (
    id UUID PRIMARY KEY,
    meeting_room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_by UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reservations_room_id ON meeting_room_reservations(meeting_room_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reservations_start_time ON meeting_room_reservations(start_time);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reservations_created_by ON meeting_room_reservations(created_by);

-- Create reservation_participants table
CREATE TABLE IF NOT EXISTS reservation_participants (
    id UUID PRIMARY KEY,
    reservation_id UUID NOT NULL REFERENCES meeting_room_reservations(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(reservation_id, employee_id)
);
CREATE INDEX IF NOT EXISTS idx_reservation_participants_reservation_id ON reservation_participants(reservation_id);
CREATE INDEX IF NOT EXISTS idx_reservation_participants_employee_id ON reservation_participants(employee_id);