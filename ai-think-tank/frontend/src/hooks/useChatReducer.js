export const chatReducer = (state, action) => {
  switch (action.type) {
    case 'START_THINKING':
      return {
        ...state,
        isThinking: true,
        messages: [...state.messages],
        experts: [],
        typingExperts: []
      };
    case 'ADD_SYSTEM_NOTICE':
      return {
        ...state,
        messages: [...state.messages, { id: Date.now(), type: 'system', message: action.payload.message }]
      };
    case 'ADD_EXPERT':
      return {
        ...state,
        experts: [...state.experts, action.payload],
        messages: [...state.messages, { id: Date.now(), type: 'join', expert: action.payload }]
      };
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, { id: Date.now(), type: 'user', message: action.payload }]
      };
    case 'SET_TYPING':
      // 避免重复加入同一个正在输入的专家
      if (!state.typingExperts.some(e => e.name === action.payload.name)) {
        return {
          ...state,
          typingExperts: [...state.typingExperts, action.payload]
        };
      }
      return state;
    case 'ADD_EXPERT_MESSAGE':
      return {
        ...state,
        typingExperts: state.typingExperts.filter(e => e.name !== action.payload.name),
        messages: [...state.messages, { id: Date.now(), type: 'expert_message', data: action.payload }]
      };
    case 'ADD_SUMMARY':
      return {
        ...state,
        messages: [...state.messages, { id: Date.now(), type: 'summary', data: action.payload }]
      };
    case 'SET_DONE':
      return {
        ...state,
        isThinking: false,
        typingExperts: []
      };
    default:
      return state;
  }
};
