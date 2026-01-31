import { ChatContainer } from './components/chat/ChatContainer'
import { Header } from './components/layout/Header'

function App() {
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header />
      <main className="flex-1 overflow-hidden">
        <ChatContainer />
      </main>
    </div>
  )
}

export default App
