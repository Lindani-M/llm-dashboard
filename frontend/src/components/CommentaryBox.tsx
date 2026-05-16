import { useState } from 'react';
import { CommentarySection } from '../types';

interface Props {
  sectionId: string;
  data: CommentarySection | undefined;
  variant?: 'box' | 'inline' | 'grantee';
  title?: string;
  onSave: (sectionId: string, content: string) => Promise<void>;
  onRevert: (sectionId: string) => Promise<void>;
}

export default function CommentaryBox({
  sectionId,
  data,
  variant = 'box',
  title,
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

  const handleRevert = async () => {
    await onRevert(sectionId);
  };

  const displayContent = (
    <span dangerouslySetInnerHTML={{ __html: data.active_content }} />
  );

  const editControls = (
    <>
      {data.is_user_override_active && !editing && (
        <div className="override-badge">✏ Manual edit</div>
      )}
      {editing ? (
        <>
          <textarea
            className="commentary-edit-textarea"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={4}
          />
          <div className="commentary-actions">
            <button className="btn-save" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button className="btn-cancel" onClick={() => setEditing(false)}>
              Cancel
            </button>
            {data.is_user_override_active && (
              <button className="btn-revert" onClick={handleRevert}>
                Revert to AI
              </button>
            )}
          </div>
        </>
      ) : (
        <button className="commentary-edit-btn" onClick={startEdit}>
          Edit
        </button>
      )}
    </>
  );

  if (variant === 'box') {
    return (
      <div className="commentary-box">
        {title && <h4>{title}</h4>}
        {data.is_user_override_active && !editing && (
          <div className="override-badge">✏ Manual edit active — AI commentary available</div>
        )}
        {editing ? (
          <>
            <textarea
              className="commentary-edit-textarea"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={5}
            />
            <div className="commentary-actions">
              <button className="btn-save" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button className="btn-cancel" onClick={() => setEditing(false)}>
                Cancel
              </button>
              {data.is_user_override_active && (
                <button className="btn-revert" onClick={handleRevert}>
                  Revert to AI
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            <p className="commentary-text">{displayContent}</p>
            <button className="commentary-edit-btn" onClick={startEdit}>
              Edit
            </button>
          </>
        )}
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div className="inline-commentary">
        {data.is_user_override_active && !editing && (
          <div className="override-badge">✏ Manual edit</div>
        )}
        {editing ? (
          <>
            <textarea
              className="commentary-edit-textarea"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={3}
            />
            <div className="commentary-actions">
              <button className="btn-save" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button className="btn-cancel" onClick={() => setEditing(false)}>
                Cancel
              </button>
              {data.is_user_override_active && (
                <button className="btn-revert" onClick={handleRevert}>
                  Revert to AI
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            {displayContent}
            <button className="commentary-edit-btn" onClick={startEdit}>
              Edit
            </button>
          </>
        )}
      </div>
    );
  }

  // variant === 'grantee' — dark card body text
  return (
    <div className="grantee-body">
      {data.is_user_override_active && !editing && (
        <div className="override-badge" style={{ color: '#c9a94e', background: 'rgba(201,169,78,0.15)' }}>
          ✏ Manual edit
        </div>
      )}
      {editing ? (
        <>
          <textarea
            className="commentary-edit-textarea"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={3}
            style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', borderColor: '#c9a94e' }}
          />
          <div className="commentary-actions">
            <button className="btn-save" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button className="btn-cancel" onClick={() => setEditing(false)}>
              Cancel
            </button>
            {data.is_user_override_active && (
              <button className="btn-revert" onClick={handleRevert}>
                Revert to AI
              </button>
            )}
          </div>
        </>
      ) : (
        <>
          {displayContent}
          <button
            className="commentary-edit-btn"
            onClick={startEdit}
          >
            Edit
          </button>
        </>
      )}
    </div>
  );
}
