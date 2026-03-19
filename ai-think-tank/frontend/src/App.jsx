import React from 'react';
import ChatWindow from './components/ChatWindow';
import './App.css';

function App() {
  return (
    <div className="app-background">
      <div className="glass-container">
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
