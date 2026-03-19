import React, { useReducer, useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { chatReducer } from '../hooks/useChatReducer';
import { useSSE } from '../hooks/useSSE';
import { SystemNotice, JoinNotice, UserMessage, ExpertMessage, SummaryCard, TypingIndicator } from './Messages';

const ChatWindow = () => {
  const [state, dispatch] = useReducer(chatReducer, {
    messages: [],
    experts: [],
    typingExperts: [],
    isThinking: false
  });
  
  const { startAnalysis } = useSSE(dispatch);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [state.messages, state.typingExperts]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || state.isThinking) return;
    
    startAnalysis(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AI 智囊团</h1>
        <span className="online-count">· 在线 {state.experts.length + 1} 人</span>
      </div>

      <div className="chat-messages">
        {state.messages.map((msg, i) => {
          switch (msg.type) {
            case 'system':
              return <SystemNotice key={i} message={msg} />;
            case 'join':
              return <JoinNotice key={i} expert={msg.expert} />;
            case 'user':
              return <UserMessage key={i} message={msg.message} />;
            case 'expert_message':
              return <ExpertMessage key={i} data={msg.data} />;
            case 'summary':
              return <SummaryCard key={i} data={msg.data} />;
            default:
              return null;
          }
        })}
        
        {state.typingExperts.map((expert, i) => (
          <TypingIndicator key={`typing-${i}`} expert={expert} />
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="请输入您的问题..."
            disabled={state.isThinking}
          />
          <button type="submit" disabled={state.isThinking || !input.trim()}>
             {state.isThinking ? <Loader2 className="spinner" size={18} /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatWindow;
