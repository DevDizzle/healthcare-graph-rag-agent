import { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Calling the ADK backend running on port 8000
      // Adjust the endpoint path based on your exact ADK serving setup
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Extract the response message depending on the ADK return format
      const reply = data.reply || data.response || JSON.stringify(data);
      
      const botMessage = { role: 'bot', content: reply };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error fetching from ADK backend:', error);
      setMessages((prev) => [...prev, { role: 'bot', content: 'Sorry, I encountered an error communicating with the backend.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Smart Hospital Network Agent</h1>
        <p>Ask me about providers, clinics, and hospitals.</p>
      </header>
      
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : 'Agent'}: </strong>
            {msg.content}
          </div>
        ))}
        {isLoading && <div className="message bot"><em>Agent is thinking...</em></div>}
      </div>

      <div className="input-box">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="e.g. Which clinics is Dr. Provider 1 affiliated with?"
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;