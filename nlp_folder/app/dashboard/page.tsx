'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  metadata?: any;
}

interface Transaction {
  id: string;
  type: string;
  amount: number;
  date: string;
  status: string;
  description: string;
}

interface Ticket {
  id: string;
  title: string;
  status: 'open' | 'in-progress' | 'closed';
  priority: 'low' | 'medium' | 'high';
  createdAt: string;
  description: string;
}

interface Meeting {
  id: string;
  title: string;
  date: string;
  time: string;
  participants: string[];
  status: 'scheduled' | 'completed' | 'cancelled';
}

export default function Dashboard() {
  const [userName, setUserName] = useState('User');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Dialog states
  const [financeDialog, setFinanceDialog] = useState(false);
  const [ticketsDialog, setTicketsDialog] = useState(false);
  const [meetsDialog, setMeetsDialog] = useState(false);
  const [accessDialog, setAccessDialog] = useState(false);

  // Data states
  const [transactions, setTransactions] = useState<Transaction[]>([
    {
      id: '1',
      type: 'expense',
      amount: 1500,
      date: '2026-02-10',
      status: 'completed',
      description: 'Office Supplies'
    },
    {
      id: '2',
      type: 'income',
      amount: 5000,
      date: '2026-02-09',
      status: 'completed',
      description: 'Client Payment'
    },
    {
      id: '3',
      type: 'expense',
      amount: 800,
      date: '2026-02-08',
      status: 'pending',
      description: 'Software License'
    }
  ]);

  const [tickets, setTickets] = useState<Ticket[]>([
    {
      id: '1',
      title: 'System Login Issue',
      status: 'in-progress',
      priority: 'high',
      createdAt: '2026-02-12',
      description: 'Users unable to login to the system'
    },
    {
      id: '2',
      title: 'Email Configuration',
      status: 'open',
      priority: 'medium',
      createdAt: '2026-02-11',
      description: 'Need to setup email forwarding'
    },
    {
      id: '3',
      title: 'Access Request',
      status: 'closed',
      priority: 'low',
      createdAt: '2026-02-10',
      description: 'Database access for new employee'
    }
  ]);

  const [meetings, setMeetings] = useState<Meeting[]>([
    {
      id: '1',
      title: 'Project Review',
      date: '2026-02-14',
      time: '10:00 AM',
      participants: ['Alex Chen', 'John Doe'],
      status: 'scheduled'
    },
    {
      id: '2',
      title: 'Team Standup',
      date: '2026-02-13',
      time: '9:00 AM',
      participants: ['Alex Chen', 'Sarah Smith', 'Mike Johnson'],
      status: 'completed'
    }
  ]);

  // New ticket form state
  const [newTicket, setNewTicket] = useState({
    title: '',
    priority: 'medium',
    description: ''
  });

  // New transaction form state
  const [newTransaction, setNewTransaction] = useState({
    type: 'expense',
    amount: '',
    description: ''
  });

  useEffect(() => {
    // Retrieve user from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        const name = parsed.username || parsed.name || 'User';
        setUserName(name);
        
        // Add welcome message
        setMessages([{
          id: 'welcome',
          text: `Hello ${name}, how can I help you today?`,
          isUser: false,
          timestamp: new Date()
        }]);
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      text: input,
      isUser: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);
    
    try {
      // Call your ML model API endpoint here
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: currentInput,
          user: userName,
          conversationHistory: messages.map(m => ({
            role: m.isUser ? 'user' : 'assistant',
            content: m.text
          }))
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response');
      }
      
      const data = await response.json();
      
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        text: data.reply || data.message || "I'm here to help! How can I assist you?",
        isUser: false,
        timestamp: new Date(),
        metadata: data.metadata
      };
      
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        text: "I'm having trouble connecting right now. Please try again in a moment.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const newChat = () => {
    setMessages([{
      id: 'welcome',
      text: `Hello ${userName}, how can I help you today?`,
      isUser: false,
      timestamp: new Date()
    }]);
    setInput('');
  };

  const handleLogout = () => {
    // Clear user from localStorage
    localStorage.removeItem('user');
    
    // Optional: Clear other app data
    // localStorage.clear(); // Uncomment to clear all localStorage
    
    // Redirect to login page or home page
    // Update the path based on your app's routing
    window.location.href = '/'; // or '/login' depending on your setup
  };

  const createTicket = () => {
    if (!newTicket.title || !newTicket.description) return;

    const ticket: Ticket = {
      id: `ticket-${Date.now()}`,
      title: newTicket.title,
      status: 'open',
      priority: newTicket.priority as 'low' | 'medium' | 'high',
      createdAt: new Date().toISOString().split('T')[0],
      description: newTicket.description
    };

    setTickets(prev => [ticket, ...prev]);
    setNewTicket({ title: '', priority: 'medium', description: '' });
  };

  const addTransaction = () => {
    if (!newTransaction.amount || !newTransaction.description) return;

    const transaction: Transaction = {
      id: `txn-${Date.now()}`,
      type: newTransaction.type,
      amount: parseFloat(newTransaction.amount),
      date: new Date().toISOString().split('T')[0],
      status: 'pending',
      description: newTransaction.description
    };

    setTransactions(prev => [transaction, ...prev]);
    setNewTransaction({ type: 'expense', amount: '', description: '' });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-yellow-500';
      case 'in-progress': return 'bg-blue-500';
      case 'closed': return 'bg-green-500';
      case 'completed': return 'bg-green-500';
      case 'pending': return 'bg-orange-500';
      case 'scheduled': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const NavCard = ({ icon, label, onClick }: { icon: string; label: string; onClick: () => void }) => (
    <Card 
      className="bg-slate-800/30 border-slate-700/50 hover:bg-slate-700/40 transition-all cursor-pointer h-24 flex items-center justify-center"
      onClick={onClick}
    >
      <CardContent className="p-0 flex flex-col items-center gap-2">
        <span className="text-3xl">{icon}</span>
        <span className="text-xs font-semibold text-white">{label}</span>
      </CardContent>
    </Card>
  );

  return (
    <div className="h-screen bg-[#0a0e27] flex">
      {/* Sidebar */}
      <div className="w-64 bg-[#0d1228] border-r border-slate-800/50 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800/50">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center text-white font-bold">
            H
          </div>
          <h1 className="ml-3 text-white font-bold text-lg">HCL Assistant</h1>
        </div>

        {/* User Profile */}
        <div className="p-4 border-b border-slate-800/50">
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardContent className="p-3 flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {userName.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <p className="text-white font-semibold text-sm">{userName}</p>
                <p className="text-cyan-400 text-xs">Global Innovation</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b border-slate-800/50">
          <Button 
            onClick={newChat}
            className="w-full bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 text-white"
          >
            ➕ New Chat
          </Button>
        </div>

        {/* Intelligence Hub */}
        <div className="p-4">
          <h3 className="text-cyan-400 text-xs font-bold mb-3 tracking-wider">INTELLIGENCE HUB</h3>
          <div className="grid grid-cols-2 gap-3">
            <NavCard icon="💼" label="FINANCE" onClick={() => setFinanceDialog(true)} />
            <NavCard icon="🎫" label="TICKETS" onClick={() => setTicketsDialog(true)} />
            <NavCard icon="📅" label="MEETS" onClick={() => setMeetsDialog(true)} />
            <NavCard icon="🔓" label="ACCESS" onClick={() => setAccessDialog(true)} />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="flex-1 p-4 overflow-auto">
          <h3 className="text-cyan-400 text-xs font-bold mb-3 tracking-wider">RECENT ACTIVITY</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
              <span className="text-slate-300">10:15 - System Auth</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
              <span className="text-slate-300">10:30 - Revenue Check</span>
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <div className="p-4 border-t border-slate-800/50">
          <Button 
  onClick={handleLogout}
  className="w-full bg-gradient-to-r from-slate-700 to-slate-800 
             hover:from-cyan-500/20 hover:to-blue-500/20 
             border border-slate-600 text-slate-300 
             hover:text-white hover:border-cyan-400/40 
             transition-all duration-300"
>
  🚪 Logout
</Button>

        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-auto p-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`mb-6 ${msg.isUser ? 'flex justify-end' : 'flex justify-start'}`}>
              <div className="max-w-2xl">
                <Card className={msg.isUser ? "bg-[#1a2942] border-cyan-500/30" : "bg-slate-800/50 border-slate-700/50"}>
                  <CardContent className="p-4">
                    <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    <p className="text-xs text-slate-400 mt-2">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start mb-6">
              <Card className="bg-slate-800/50 border-slate-700/50 max-w-2xl">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-slate-800/50">
          <div className="flex gap-3 items-center">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Type your request here..."
              className="flex-1 h-14 bg-[#1a2942] border-slate-700/50 text-white placeholder:text-slate-500 focus-visible:border-cyan-500 focus-visible:ring-0 rounded-full px-6"
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="h-14 w-14 bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 rounded-full shadow-lg flex items-center justify-center disabled:opacity-50"
            >
              <span className="text-xl">➤</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Finance Dialog */}
      <Dialog open={financeDialog} onOpenChange={setFinanceDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto bg-[#0d1228] border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white text-2xl flex items-center gap-2">
              💼 Finance Dashboard
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              View and manage your financial transactions
            </DialogDescription>
          </DialogHeader>
          
          <Tabs defaultValue="transactions" className="w-full">
            <TabsList className="bg-slate-800/50">
              <TabsTrigger value="transactions">Transactions</TabsTrigger>
              <TabsTrigger value="add">Add Transaction</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
            </TabsList>
            
            <TabsContent value="transactions" className="space-y-4 mt-4">
              {transactions.map((txn) => (
                <Card key={txn.id} className="bg-slate-800/30 border-slate-700/50">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-white font-semibold">{txn.description}</p>
                        <p className="text-sm text-slate-400">{txn.date}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-lg font-bold ${txn.type === 'income' ? 'text-green-400' : 'text-red-400'}`}>
                          {txn.type === 'income' ? '+' : '-'}${txn.amount.toFixed(2)}
                        </p>
                        <Badge className={`${getStatusColor(txn.status)} text-xs`}>
                          {txn.status}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
            
            <TabsContent value="add" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div>
                  <Label className="text-white">Type</Label>
                  <Select value={newTransaction.type} onValueChange={(val) => setNewTransaction({...newTransaction, type: val})}>
                    <SelectTrigger className="bg-slate-800/50 border-slate-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="expense">Expense</SelectItem>
                      <SelectItem value="income">Income</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-white">Amount</Label>
                  <Input
                    type="number"
                    value={newTransaction.amount}
                    onChange={(e) => setNewTransaction({...newTransaction, amount: e.target.value})}
                    placeholder="0.00"
                    className="bg-slate-800/50 border-slate-700 text-white"
                  />
                </div>
                <div>
                  <Label className="text-white">Description</Label>
                  <Input
                    value={newTransaction.description}
                    onChange={(e) => setNewTransaction({...newTransaction, description: e.target.value})}
                    placeholder="Enter description"
                    className="bg-slate-800/50 border-slate-700 text-white"
                  />
                </div>
                <Button onClick={addTransaction} className="w-full bg-gradient-to-r from-cyan-400 to-blue-500">
                  Add Transaction
                </Button>
              </div>
            </TabsContent>
            
            <TabsContent value="analytics" className="mt-4">
              <Card className="bg-slate-800/30 border-slate-700/50">
                <CardContent className="p-6">
                  <h3 className="text-white font-semibold mb-4">Summary</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-slate-400 text-sm">Total Income</p>
                      <p className="text-2xl font-bold text-green-400">
                        ${transactions.filter(t => t.type === 'income').reduce((acc, t) => acc + t.amount, 0).toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Total Expenses</p>
                      <p className="text-2xl font-bold text-red-400">
                        ${transactions.filter(t => t.type === 'expense').reduce((acc, t) => acc + t.amount, 0).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Tickets Dialog */}
      <Dialog open={ticketsDialog} onOpenChange={setTicketsDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto bg-[#0d1228] border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white text-2xl flex items-center gap-2">
              🎫 Support Tickets
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Create and track support tickets
            </DialogDescription>
          </DialogHeader>
          
          <Tabs defaultValue="tickets" className="w-full">
            <TabsList className="bg-slate-800/50">
              <TabsTrigger value="tickets">All Tickets</TabsTrigger>
              <TabsTrigger value="create">Create Ticket</TabsTrigger>
            </TabsList>
            
            <TabsContent value="tickets" className="space-y-4 mt-4">
              {tickets.map((ticket) => (
                <Card key={ticket.id} className="bg-slate-800/30 border-slate-700/50">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="text-white font-semibold">{ticket.title}</p>
                        <p className="text-sm text-slate-400 mt-1">{ticket.description}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge className={`${getPriorityColor(ticket.priority)} text-xs`}>
                          {ticket.priority}
                        </Badge>
                        <Badge className={`${getStatusColor(ticket.status)} text-xs`}>
                          {ticket.status}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500">Created: {ticket.createdAt}</p>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
            
            <TabsContent value="create" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div>
                  <Label className="text-white">Title</Label>
                  <Input
                    value={newTicket.title}
                    onChange={(e) => setNewTicket({...newTicket, title: e.target.value})}
                    placeholder="Enter ticket title"
                    className="bg-slate-800/50 border-slate-700 text-white"
                  />
                </div>
                <div>
                  <Label className="text-white">Priority</Label>
                  <Select value={newTicket.priority} onValueChange={(val) => setNewTicket({...newTicket, priority: val})}>
                    <SelectTrigger className="bg-slate-800/50 border-slate-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-white">Description</Label>
                  <Textarea
                    value={newTicket.description}
                    onChange={(e) => setNewTicket({...newTicket, description: e.target.value})}
                    placeholder="Describe the issue..."
                    className="bg-slate-800/50 border-slate-700 text-white min-h-[100px]"
                  />
                </div>
                <Button onClick={createTicket} className="w-full bg-gradient-to-r from-cyan-400 to-blue-500">
                  Create Ticket
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* Meetings Dialog */}
      <Dialog open={meetsDialog} onOpenChange={setMeetsDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto bg-[#0d1228] border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white text-2xl flex items-center gap-2">
              📅 Meetings
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              View and manage your meetings
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {meetings.map((meeting) => (
              <Card key={meeting.id} className="bg-slate-800/30 border-slate-700/50">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white font-semibold text-lg">{meeting.title}</p>
                      <p className="text-sm text-slate-400 mt-1">
                        📅 {meeting.date} at {meeting.time}
                      </p>
                      <p className="text-sm text-slate-400 mt-1">
                        👥 {meeting.participants.join(', ')}
                      </p>
                    </div>
                    <Badge className={`${getStatusColor(meeting.status)} text-xs`}>
                      {meeting.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Access Dialog */}
      <Dialog open={accessDialog} onOpenChange={setAccessDialog}>
        <DialogContent className="max-w-2xl bg-[#0d1228] border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white text-2xl flex items-center gap-2">
              🔓 Access Management
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Manage permissions and access controls
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardContent className="p-4">
                <h3 className="text-white font-semibold mb-3">Your Permissions</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Finance Access</span>
                    <Badge className="bg-green-500">Granted</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Ticket Management</span>
                    <Badge className="bg-green-500">Granted</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Meeting Scheduling</span>
                    <Badge className="bg-green-500">Granted</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-300">Admin Panel</span>
                    <Badge className="bg-red-500">Denied</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardContent className="p-4">
                <h3 className="text-white font-semibold mb-3">Request Access</h3>
                <p className="text-slate-400 text-sm mb-3">
                  Need additional permissions? Contact your administrator.
                </p>
                <Button className="w-full bg-gradient-to-r from-cyan-400 to-blue-500">
                  Request Access
                </Button>
              </CardContent>
            </Card>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
