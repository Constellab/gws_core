-- =============================================
-- Lab DB init file (gws_core schema)
--
-- Inserts the entities shared with the outside DB (space-init.sql) so that
-- both databases reference the same ids and consistent information.
--
-- Shared entities:
--   * Users   : outside `user` table             -> `gws_user`
--   * Lab     : outside `lab` table               -> `gws_lab` (the "localhost" lab)
--   * Folders : outside `hierarchy_object`/`folder` -> `gws_folder`
--
-- Notes on the mapping:
--   * `gws_user` has no password/status/category/company columns. The outside
--     `category` is mapped to `gws_user.group` (ADMIN -> ADMIN, USER -> USER).
--     `is_active` is derived from the outside `status` (READY -> active).
--   * The outside DB robot user is intentionally NOT imported. Instead a
--     dedicated gws_core system user (group SYSUSER) is created below — it is
--     local to this lab DB and has no counterpart in the outside DB.
--   * The outside `lab.id` is the cross-DB shared lab identifier, so it is
--     stored in `gws_lab.lab_id`. `gws_lab.id` is a local primary key.
--   * `gws_folder` is a plain hierarchy node (id, name, parent_id only). The
--     outside DB's space_id, style, storage, folder_user and lab_folder
--     associations have no column in `gws_folder` and are intentionally dropped.
-- =============================================

SET NAMES utf8mb4;
SET foreign_key_checks = 0;

-- Shared ids (same values as space-init.sql)
SET @adminUserId     = '98ed7a54-9ee4-4257-811f-e1dfe730b97d';
SET @secondaryUserId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

-- Local-only system user (no counterpart in the outside DB)
SET @sysUserId       = 'e0d9c8b7-a6f5-4e43-8d21-0c1b2a3f4e5d';

-- Shared lab id (outside DB `lab.id` -> gws_lab.lab_id)
SET @localhostLabId  = '83afdd53-2509-4dcc-82d4-86af435447dc';
SET @adminUserSpaceId = '696072d7-1eb3-4161-a6bb-d3b46d0a2b6e';

-- Shared folder ids (same values as space-init.sql)
SET @rootFolderId = 'f0a1b2c3-d4e5-6789-abcd-000000000001';
SET @subFolderId  = 'f0a1b2c3-d4e5-6789-abcd-000000000002';


-- =============================================
-- Users
-- =============================================

-- System user (local to this lab DB, not present in the outside DB).
-- gws_core requires exactly one user with group SYSUSER (User.get_and_check_sysuser).
INSERT INTO `gws_user`
  (`id`, `created_at`, `last_modified_at`, `email`, `first_name`, `last_name`,
   `group`, `is_active`, `theme`, `lang`, `photo`)
VALUES
  (@sysUserId, '2023-02-27 17:15:47', '2023-02-27 17:15:47', 'sysuser@gencovery.com',
   'System', 'User', 'SYSUSER', 1, 'light-theme', 'en', NULL);

-- Test user (Admin) - Michel Larousse
INSERT INTO `gws_user`
  (`id`, `created_at`, `last_modified_at`, `email`, `first_name`, `last_name`,
   `group`, `is_active`, `theme`, `lang`, `photo`)
VALUES
  (@adminUserId, '2023-02-27 17:15:47', '2023-02-27 17:15:47', 'test@gencovery.com',
   'Michel', 'Larousse', 'ADMIN', 1, 'light-theme', 'en', NULL);

-- Secondary user (non-admin) - Sophie Dupont
INSERT INTO `gws_user`
  (`id`, `created_at`, `last_modified_at`, `email`, `first_name`, `last_name`,
   `group`, `is_active`, `theme`, `lang`, `photo`)
VALUES
  (@secondaryUserId, '2023-03-15 10:00:00', '2023-03-15 10:00:00', 'sophie@gencovery.com',
   'Sophie', 'Dupont', 'USER', 1, 'light-theme', 'en', NULL);


-- =============================================
-- Lab
-- =============================================

-- The "localhost" lab.
-- `lab_id` holds the shared id from the outside DB; `id` is the local PK.
-- mode = prod, environment = ON_CLOUD (outside DB lab type is CLOUD).
INSERT INTO `gws_lab`
  (`id`, `created_at`, `last_modified_at`, `lab_id`, `name`, `mode`, `environment`,
   `domain`, `space_id`, `space_name`, `credentials_id`)
VALUES
  ('c7e4f9a1-6b2d-4e83-9f15-2a8c0d1e3b47', '2025-08-19 16:49:37', '2025-10-07 15:55:38',
   @localhostLabId, 'localhost', 'prod', 'ON_CLOUD',
   'localhost.gencovery.io', @adminUserSpaceId, 'Michel Larousse', NULL);


-- =============================================
-- Folders
-- =============================================

-- Root folder "Research Project" (no parent).
INSERT INTO `gws_folder`
  (`id`, `created_at`, `last_modified_at`, `name`, `parent_id`)
VALUES
  (@rootFolderId, '2026-01-10 10:00:00', '2026-01-10 10:00:00', 'Research Project', NULL);

-- Sub folder "Experiments" (child of the root folder).
INSERT INTO `gws_folder`
  (`id`, `created_at`, `last_modified_at`, `name`, `parent_id`)
VALUES
  (@subFolderId, '2026-01-10 10:30:00', '2026-01-10 10:30:00', 'Experiments', @rootFolderId);

SET foreign_key_checks = 1;
