import { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles, UserPen, Eye, EyeOff } from 'lucide-react';

/**
 * FormField — renders an input/textarea/select with AI-origin highlighting,
 * confidence tags, source snippets, and change animation.
 * Uses Lucide icons for all indicators.
 */
export default function FormField({
  label,
  required,
  fieldName,
  fieldData,
  onChange,
  disabled,
  isChanged,
  type = 'text',
  options = [],
  maxLength,
  placeholder = '',
}) {
  const [showSnippet, setShowSnippet] = useState(false);
  const value = fieldData?.value ?? '';
  const confidence = fieldData?.confidence;
  const origin = fieldData?.origin;
  const sourceSnippet = fieldData?.source_snippet;

  // Build CSS classes for field highlighting
  const fieldClasses = ['form-field'];
  if (origin === 'ai' && value) fieldClasses.push('ai-origin');
  if (confidence && value) fieldClasses.push(`confidence-${confidence}`);
  if (isChanged) fieldClasses.push('just-changed');

  const handleChange = (e) => {
    onChange(fieldName, e.target.value);
  };

  const renderInput = () => {
    if (type === 'textarea') {
      return (
        <div style={{ position: 'relative' }}>
          <textarea
            value={value}
            onChange={handleChange}
            disabled={disabled}
            placeholder={placeholder}
            maxLength={maxLength}
            rows={4}
          />
          {maxLength && (
            <span className="char-count">{value.length}/{maxLength}</span>
          )}
        </div>
      );
    }

    if (type === 'select') {
      return (
        <select value={value} onChange={handleChange} disabled={disabled}>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt || placeholder || '— Select —'}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type={type}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        placeholder={placeholder}
      />
    );
  };

  return (
    <div className={fieldClasses.join(' ')}>
      <label>
        {label}
        {required && <span className="required">*</span>}
      </label>

      {renderInput()}

      {/* Field metadata row (confidence + origin tags) */}
      {value && (confidence || origin) && (
        <div className="field-meta">
          {confidence && (
            <span className={`field-confidence-tag ${confidence}`}>
              {confidence === 'high' ? '●' : confidence === 'medium' ? '◐' : '○'}{' '}
              {confidence}
            </span>
          )}
          {origin && (
            <span className="field-origin-tag">
              <span className={`dot ${origin}`}></span>
              {origin === 'ai' ? (
                <><Sparkles size={10} style={{ marginRight: '2px' }} /> AI extracted</>
              ) : (
                <><UserPen size={10} style={{ marginRight: '2px' }} /> Human edited</>
              )}
            </span>
          )}
          {sourceSnippet && (
            <button
              className="btn btn-ghost btn-sm"
              style={{ padding: '2px 8px', fontSize: '10px', gap: '3px' }}
              onClick={() => setShowSnippet(!showSnippet)}
              title="View source snippet"
            >
              {showSnippet ? <EyeOff size={10} /> : <Eye size={10} />}
              {showSnippet ? 'Hide' : 'Source'}
            </button>
          )}
        </div>
      )}

      {/* Source snippet (provenance) */}
      {showSnippet && sourceSnippet && (
        <div className="field-source-snippet">
          "{sourceSnippet}"
        </div>
      )}
    </div>
  );
}
