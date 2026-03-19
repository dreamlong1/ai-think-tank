import React from 'react';
import { motion as Motion } from 'framer-motion';

export const SystemNotice = ({ message }) => (
  <Motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="system-notice"
  >
    {message.message}
  </Motion.div>
);

export const JoinNotice = ({ expert }) => (
  <Motion.div
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    className="join-notice"
  >
    <div className="line" />
    <span>{expert.avatar_emoji} {expert.name} 加入了讨论</span>
    <div className="line" />
  </Motion.div>
);

export const UserMessage = ({ message }) => (
  <Motion.div
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    className="message-wrapper user-wrapper"
  >
    <div className="message-bubble user-bubble">
      {message}
    </div>
    <div className="avatar user-avatar">🧑</div>
  </Motion.div>
);

export const ExpertMessage = ({ data }) => {
  return (
    <Motion.div
      initial={{ opacity: 0, x: -20, y: 10 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 15 }}
      className="message-wrapper expert-wrapper"
    >
      <div className="avatar expert-avatar">{data.avatar_emoji}</div>
      <div className="expert-content">
        <div className="expert-name">{data.name}</div>
        <div className="message-bubble expert-bubble">
          <div className="message-meta">
            <details open>
              <summary>📌 核心观点</summary>
              <ul>
                {data.key_points.map((pt, i) => <li key={i}>{pt}</li>)}
              </ul>
            </details>
          </div>
          <p className="message-text">{data.message}</p>
          <div className="conclusion">结论：{data.conclusion}</div>
        </div>
      </div>
    </Motion.div>
  );
};

export const SummaryCard = ({ data }) => (
  <Motion.div
    initial={{ opacity: 0, y: 30 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.2 }}
    className="summary-card"
  >
    <div className="summary-header">
      📋 综合分析报告
    </div>
    <div className="summary-body">
      <div className="summary-section">
        <h3>✅ 共识</h3>
        <p>{data.consensus}</p>
      </div>
      <div className="summary-section">
        <h3>⚡ 分歧</h3>
        <p>{data.disagreements}</p>
      </div>
      <div className="summary-section">
        <h3>🔍 盲点</h3>
        <p>{data.blind_spots}</p>
      </div>
      <div className="summary-section highlight">
        <h3>📝 综合结论</h3>
        <p>{data.conclusion}</p>
      </div>
    </div>
  </Motion.div>
);

export const TypingIndicator = ({ expert }) => (
  <Motion.div
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.8 }}
    className="typing-indicator"
  >
    <div className="avatar">{expert.avatar_emoji}</div>
    <div className="typing-bubble">
      <div className="dot" />
      <div className="dot" />
      <div className="dot" />
    </div>
  </Motion.div>
);
