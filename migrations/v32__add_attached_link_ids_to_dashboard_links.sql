ALTER TABLE dashboard_links
ADD COLUMN IF NOT EXISTS attached_link_ids INTEGER[];

COMMENT ON COLUMN dashboard_links.attached_link_ids IS
  'IDs of up to 2 sibling dashboard links (same client) that viewers can toggle between in the public view';
