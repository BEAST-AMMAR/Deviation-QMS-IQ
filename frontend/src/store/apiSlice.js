import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const API_BASE = '/api';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: API_BASE }),
  tagTypes: ['Draft', 'Deviation'],
  endpoints: (builder) => ({

    // POST /drafts — create new draft
    createDraft: builder.mutation({
      query: () => ({ url: '/drafts', method: 'POST' }),
    }),

    // GET /drafts/{id}
    getDraft: builder.query({
      query: (draftId) => `/drafts/${draftId}`,
      providesTags: ['Draft'],
    }),

    // POST /drafts/{id}/message
    sendMessage: builder.mutation({
      query: ({ draftId, text }) => ({
        url: `/drafts/${draftId}/message`,
        method: 'POST',
        body: { text },
      }),
      invalidatesTags: ['Draft'],
    }),

    // POST /drafts/{id}/upload
    uploadFile: builder.mutation({
      query: ({ draftId, file }) => {
        const formData = new FormData();
        formData.append('file', file);
        return {
          url: `/drafts/${draftId}/upload`,
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['Draft'],
    }),

    // POST /drafts/{id}/confirm
    confirmAssessment: builder.mutation({
      query: ({ draftId, assessment }) => ({
        url: `/drafts/${draftId}/confirm`,
        method: 'POST',
        body: assessment,
      }),
      invalidatesTags: ['Draft', 'Deviation'],
    }),

    // PATCH /drafts/{id}/fields
    updateDraftFields: builder.mutation({
      query: ({ draftId, fieldName, value, fields }) => ({
        url: `/drafts/${draftId}/fields`,
        method: 'PATCH',
        body: fields ? { fields } : { field_name: fieldName, value },
      }),
      invalidatesTags: ['Draft'],
    }),

    // POST /drafts/{id}/commit
    commitDirect: builder.mutation({
      query: ({ draftId, ...payload }) => ({
        url: `/drafts/${draftId}/commit`,
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: ['Draft', 'Deviation'],
    }),

    // POST /drafts/{id}/reset
    resetDraft: builder.mutation({
      query: (draftId) => ({
        url: `/drafts/${draftId}/reset`,
        method: 'POST',
      }),
      invalidatesTags: ['Draft'],
    }),

    // GET /deviations
    listDeviations: builder.query({
      query: () => '/deviations',
      providesTags: ['Deviation'],
    }),

    // GET /deviations/{id}
    getDeviation: builder.query({
      query: (id) => `/deviations/${id}`,
      providesTags: ['Deviation'],
    }),

    // GET /deviations/{id}/events
    getDeviationEvents: builder.query({
      query: (id) => `/deviations/${id}/events`,
      providesTags: ['Deviation'],
    }),

    // GET /deviations/{id}/session — Complete chat transcript, report outcomes, and audit trail
    getSessionDetail: builder.query({
      query: (id) => `/deviations/${id}/session`,
      providesTags: ['Deviation'],
    }),
  }),
});

export const {
  useCreateDraftMutation,
  useGetDraftQuery,
  useSendMessageMutation,
  useUploadFileMutation,
  useConfirmAssessmentMutation,
  useUpdateDraftFieldsMutation,
  useCommitDirectMutation,
  useResetDraftMutation,
  useListDeviationsQuery,
  useGetDeviationQuery,
  useGetDeviationEventsQuery,
  useGetSessionDetailQuery,
} = apiSlice;

