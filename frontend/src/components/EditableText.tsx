import { useState } from 'react';
import { CommentarySection } from '../types';

interface Props {
  sectionId: string;
  data: CommentarySection | undefined;
  multiline?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onSave: (sectionId: string, content: string) => Promise<void>;
  onRevert: (sectionId: string) => Promise<void>;
}

export default function EditableText({
  sectionId,
  data,
  multiline = false,
  className,
  style,
  onSave,
  onRevert,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);

  if (!data) return null;

  const startEdit = () => {
    setDraft(data.active_content);
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(sectionId, draft);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !multiline) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      setEditing(false);
    }
  };

  if (editing) {
    return (
      <span className="editable-text-editing">
        {multiline ? (
          <textarea
            className="editable-text-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={2}
            autoFocus
          />
        ) : (
          <input
            className="editable-text-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
          />
        )}
        <span className="editable-text-actions">
          <button className="btn-save" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button className="btn-cancel" onClick={() => setEditing(false)}>
            Cancel
          </button>
          {data.is_user_override_active && (
            <button
              className="btn-revert"
              onClick={() => {
                onRevert(sectionId);
                setEditing(false);
              }}
            >
              Revert
            </button>
          )}
        </span>
      </span>
    );
  }

  return (
    <span
      className={`editable-text-wrap${className ? ` ${className}` : ''}`}
      style={style}
    >
      {data.active_content}
      <button className="commentary-edit-btn editable-edit-btn" onClick={startEdit}>Edit</button>
    </span>
  );
}
