import { createSlice } from '@reduxjs/toolkit';

/*
 * Draft Slice — form field values + per-field metadata + status
 * Matches TDD §6 exactly.
 */

const emptyField = () => ({
  value: null,
  confidence: null,
  source_snippet: null,
  origin: null, // 'ai' | 'human' | null
});

const initialState = {
  draftId: null,
  status: 'idle', // idle | pending_triage | extracting | awaiting_confirmation | ready_to_commit | committed
  fields: {
    site_plant: emptyField(),
    date_of_occurrence: emptyField(),
    title: emptyField(),
    source: emptyField(),
    related_product: emptyField(),
    batch_lot: emptyField(),
    detailed_description: emptyField(),
    initial_impact: emptyField(),
    initial_severity: emptyField(),
  },
  pendingAssessment: null,
  changedFields: [],
  isLoading: false,
};

const draftSlice = createSlice({
  name: 'draft',
  initialState,
  reducers: {
    setDraftId(state, action) {
      state.draftId = action.payload;
      state.status = 'pending_triage';
    },

    setFieldsFromResponse(state, action) {
      const { fields, changedFields, pendingAssessment, status } = action.payload;
      if (fields) {
        Object.keys(fields).forEach((key) => {
          if (state.fields[key] !== undefined && fields[key]) {
            state.fields[key] = {
              value: fields[key].value ?? state.fields[key].value,
              confidence: fields[key].confidence ?? state.fields[key].confidence,
              source_snippet: fields[key].source_snippet ?? state.fields[key].source_snippet,
              origin: fields[key].origin ?? state.fields[key].origin,
            };
          }
        });
      }
      if (changedFields) state.changedFields = changedFields;
      if (pendingAssessment) {
        state.pendingAssessment = pendingAssessment;
        state.status = 'awaiting_confirmation';
      }
      if (status === 'committed') {
        state.status = 'committed';
      } else if (pendingAssessment) {
        state.status = 'awaiting_confirmation';
      } else if (status) {
        state.status = status;
      }
    },

    updateFieldManually(state, action) {
      const { fieldName, value } = action.payload;
      if (state.fields[fieldName] !== undefined) {
        state.fields[fieldName] = {
          ...state.fields[fieldName],
          value,
          origin: 'human',
          confidence: 'high',
        };
      }
    },

    setStatus(state, action) {
      state.status = action.payload;
    },

    setLoading(state, action) {
      state.isLoading = action.payload;
    },

    setCommitted(state) {
      state.status = 'committed';
      state.pendingAssessment = null;
    },

    clearChangedFields(state) {
      state.changedFields = [];
    },

    resetDraft() {
      return { ...initialState };
    },
  },
});

export const {
  setDraftId,
  setFieldsFromResponse,
  updateFieldManually,
  setStatus,
  setLoading,
  setCommitted,
  clearChangedFields,
  resetDraft,
} = draftSlice.actions;

export default draftSlice.reducer;
