import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const API_BASE = '/api';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE,
    prepareHeaders: (headers, { getState }) => {
      const state = getState();
      const token = state.auth?.token || localStorage.getItem('deviationiq_token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Draft', 'Deviation', 'User'],
  endpoints: (builder) => ({

    // --- Authentication ---
    login: builder.mutation({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User'],
    }),

    register: builder.mutation({
      query: (newUser) => ({
        url: '/auth/register',
        method: 'POST',
        body: newUser,
      }),
      invalidatesTags: ['User'],
    }),

    getMe: builder.query({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),

    logoutApi: builder.mutation({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),

    // --- Drafts & AI Pipeline ---
    createDraft: builder.mutation({
      query: () => ({ url: '/drafts', method: 'POST' }),
    }),

    getDraft: builder.query({
      query: (draftId) => `/drafts/${draftId}`,
      providesTags: ['Draft'],
    }),

    sendMessage: builder.mutation({
      query: ({ draftId, text }) => ({
        url: `/drafts/${draftId}/message`,
        method: 'POST',
        body: { text },
      }),
      invalidatesTags: ['Draft'],
    }),

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

    confirmAssessment: builder.mutation({
      query: ({ draftId, assessment }) => ({
        url: `/drafts/${draftId}/confirm`,
        method: 'POST',
        body: assessment,
      }),
      invalidatesTags: ['Draft', 'Deviation'],
    }),

    updateDraftFields: builder.mutation({
      query: ({ draftId, fieldName, value, fields }) => ({
        url: `/drafts/${draftId}/fields`,
        method: 'PATCH',
        body: fields ? { fields } : { field_name: fieldName, value },
      }),
      invalidatesTags: ['Draft'],
    }),

    commitDirect: builder.mutation({
      query: ({ draftId, ...payload }) => ({
        url: `/drafts/${draftId}/commit`,
        method: 'POST',
        body: payload,
      }),
      invalidatesTags: ['Draft', 'Deviation'],
    }),

    resetDraft: builder.mutation({
      query: (draftId) => ({
        url: `/drafts/${draftId}/reset`,
        method: 'POST',
      }),
      invalidatesTags: ['Draft'],
    }),

    // --- Deviations ---
    listDeviations: builder.query({
      query: () => '/deviations',
      providesTags: ['Deviation'],
    }),

    getDeviation: builder.query({
      query: (id) => `/deviations/${id}`,
      providesTags: ['Deviation'],
    }),

    getDeviationEvents: builder.query({
      query: (id) => `/deviations/${id}/events`,
      providesTags: ['Deviation'],
    }),

    getSessionDetail: builder.query({
      query: (id) => `/deviations/${id}/session`,
      providesTags: ['Deviation'],
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useGetMeQuery,
  useLogoutApiMutation,
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
