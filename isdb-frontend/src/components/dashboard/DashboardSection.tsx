import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollToTop } from "../ScrollToTop";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Interface for message types
interface UseCaseMessage {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  structuredResponse?: {
    calculations?: Array<{label: string, value: number}>;
    journal_entries?: Array<{debit?: string, credit?: string, amount: number}>;
    ledger_summary?: Array<{[key: string]: string | number}>;
    explanation?: string;
  };
  timestamp?: number;
}

interface ReverseTransactionMessage {
  role: "user" | "assistant";
  content: string;
  response?: {
    applicable_standards: Array<{standard: string, reason: string, weight: number}>;
    primary_standard: string;
    primary_sharia_standard: string;
    detailed_justification: string;
    thinking_process: string[];
    anomalies: string[];
  };
  timestamp?: number;
}

// Interface for transaction statistics
interface TransactionType {
  name: string;
  count: number;
}

export default function DashboardSection() {
  // State for storing statistics
  const [useCaseStats, setUseCaseStats] = useState({
    totalConversations: 0,
    userMessages: 0,
    assistantMessages: 0,
    averageResponseLength: 0,
    averageResponseTime: 0,
    topKeywords: [] as {word: string, count: number}[]
  });
  
  const [reverseTransactionStats, setReverseTransactionStats] = useState({
    totalTransactions: 0,
    standardsAnalyzed: 0,
    transactionTypes: [] as TransactionType[],
    anomaliesDetected: 0
  });
  
  const [recentQueries, setRecentQueries] = useState<{content: string, date: string, time: string, transactionData: string, type: 'useCase' | 'reverseTransaction'}[]>([]);

  // Load and process data from localStorage
  useEffect(() => {
    // Process UseCase chat history
    const useCaseHistory = localStorage.getItem('useCaseChatHistory');
    if (useCaseHistory) {
      try {
        const messages = JSON.parse(useCaseHistory) as UseCaseMessage[];
        
        // Calculate statistics
        const userMsgs = messages.filter(msg => msg.role === 'user');
        const assistantMsgs = messages.filter(msg => msg.role === 'assistant');
        
        // Calculate average response length
        const totalLength = assistantMsgs.reduce((sum, msg) => sum + msg.content.length, 0);
        const avgLength = assistantMsgs.length > 0 ? Math.round(totalLength / assistantMsgs.length) : 0;
        
        // Calculate average response time (if timestamps are available)
        let avgResponseTime = 0;
        let responseTimes = 0;
        let totalResponseTime = 0;
        
        // Add timestamps to messages if they don't exist (for future tracking)
        const now = Date.now();
        const messagesWithTimestamps = messages.map((msg, i) => {
          if (!msg.timestamp) {
            // Simulate timestamps with 30 second intervals from now
            return { ...msg, timestamp: now - (messages.length - i) * 30000 };
          }
          return msg;
        });
        
        // Calculate response times between user and assistant messages
        for (let i = 1; i < messagesWithTimestamps.length; i++) {
          const current = messagesWithTimestamps[i];
          const prev = messagesWithTimestamps[i-1];
          
          if (current.role === 'assistant' && prev.role === 'user' && 
              current.timestamp && prev.timestamp) {
            const responseTime = (current.timestamp - prev.timestamp) / 1000; // in seconds
            if (responseTime > 0 && responseTime < 300) { // Ignore unrealistic times (>5 min)
              totalResponseTime += responseTime;
              responseTimes++;
            }
          }
        }
        
        if (responseTimes > 0) {
          avgResponseTime = Math.round(totalResponseTime / responseTimes);
        }
        
        // Save messages with timestamps back to localStorage for future use
        if (messagesWithTimestamps.some(msg => !msg.timestamp)) {
          localStorage.setItem('useCaseChatHistory', JSON.stringify(messagesWithTimestamps));
        }
        
        // Extract keywords (simple implementation - count words with 4+ characters)
        const allText = userMsgs.map(msg => msg.content).join(' ').toLowerCase();
        const words = allText.match(/\b\w{4,}\b/g) || [];
        const wordCounts: {[key: string]: number} = {};
        
        words.forEach(word => {
          if (wordCounts[word]) {
            wordCounts[word]++;
          } else {
            wordCounts[word] = 1;
          }
        });
        
        const topKeywords = Object.entries(wordCounts)
          .map(([word, count]) => ({ word, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
        
        // Get recent queries with transaction data
        const useCaseQueries = userMsgs.slice(-5).map(msg => {
          // Find the corresponding assistant response
          const assistantIdx = messages.findIndex((m, i) => 
            i > messages.indexOf(msg) && m.role === 'assistant'
          );
          
          const assistantMsg = assistantIdx !== -1 ? messages[assistantIdx] : null;
          let transactionData = 'N/A';
          
          // Extract transaction data from structured response if available
          if (assistantMsg?.structuredResponse) {
            if (assistantMsg.structuredResponse.calculations?.length) {
              transactionData = `${assistantMsg.structuredResponse.calculations.length} calculations`;
            } else if (assistantMsg.structuredResponse.journal_entries?.length) {
              transactionData = `${assistantMsg.structuredResponse.journal_entries.length} journal entries`;
            } else if (assistantMsg.structuredResponse.ledger_summary?.length) {
              transactionData = `${assistantMsg.structuredResponse.ledger_summary.length} ledger items`;
            }
          }
          
          // Format timestamp
          const timestamp = msg.timestamp ? new Date(msg.timestamp) : new Date();
          
          return {
            content: msg.content.length > 50 ? msg.content.substring(0, 50) + '...' : msg.content,
            date: timestamp.toLocaleDateString(),
            time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            transactionData,
            type: 'useCase' as const
          };
        });
        
        setUseCaseStats({
          totalConversations: userMsgs.length,
          userMessages: userMsgs.length,
          assistantMessages: assistantMsgs.length,
          averageResponseLength: avgLength,
          averageResponseTime: avgResponseTime,
          topKeywords
        });
        // Add UseCase queries to the recent queries state
        if (useCaseQueries.length > 0) {
          setRecentQueries(prevQueries => {
            const allQueries = [...prevQueries, ...useCaseQueries];
            return allQueries
              .sort((a, b) => {
                const dateA = new Date(`${a.date} ${a.time}`);
                const dateB = new Date(`${b.date} ${b.time}`);
                return dateB.getTime() - dateA.getTime();
              })
              .slice(0, 10);
          });
        }
      } catch (error) {
        console.error('Error parsing UseCase history:', error);
      }
    }
    
    // Process ReverseTransaction chat history
    const reverseHistory = localStorage.getItem('reverseTransactionChatHistory');
    if (reverseHistory) {
      try {
        const messages = JSON.parse(reverseHistory) as ReverseTransactionMessage[];
        
        // Count transactions and extract types
        const transactions = messages.filter(msg => msg.role === 'assistant' && msg.response);
        
        // Add timestamps to messages if they don't exist (for future tracking)
        const now = Date.now();
        const messagesWithTimestamps = messages.map((msg, i) => {
          if (!msg.timestamp) {
            // Simulate timestamps with 30 second intervals from now
            return { ...msg, timestamp: now - (messages.length - i) * 30000 };
          }
          return msg;
        });
        
        // Save messages with timestamps back to localStorage for future use
        if (messagesWithTimestamps.some(msg => !msg.timestamp)) {
          localStorage.setItem('reverseTransactionChatHistory', JSON.stringify(messagesWithTimestamps));
        }
        
        // Count standards analyzed and anomalies
        let standardsCount = 0;
        let anomaliesCount = 0;
        const transactionTypeMap: {[key: string]: number} = {};
        
        // Get recent queries from reverse transactions
        const reverseTransactionQueries = messages
          .filter(msg => msg.role === 'user')
          .slice(-5)
          .map(msg => {
            // Find the corresponding assistant response
            const assistantIdx = messages.findIndex((m, i) => 
              i > messages.indexOf(msg) && m.role === 'assistant'
            );
            
            const assistantMsg = assistantIdx !== -1 ? messages[assistantIdx] : null;
            let transactionData = 'N/A';
            
            // Extract transaction data - number of anomalies if available
            if (assistantMsg?.response?.anomalies) {
              transactionData = `${assistantMsg.response.anomalies.length} anomalies`;
            }
            
            // Format timestamp
            const timestamp = msg.timestamp ? new Date(msg.timestamp) : new Date();
            
            return {
              content: msg.content.length > 50 ? msg.content.substring(0, 50) + '...' : msg.content,
              date: timestamp.toLocaleDateString(),
              time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              transactionData,
              type: 'reverseTransaction' as const
            };
          });
        
        transactions.forEach(transaction => {
          if (transaction.response) {
            // Count standards
            if (transaction.response.applicable_standards) {
              standardsCount += transaction.response.applicable_standards.length;
            }
            
            // Count anomalies
            if (transaction.response.anomalies && transaction.response.anomalies.length > 0) {
              anomaliesCount += transaction.response.anomalies.length;
            }
            
            // Track transaction types (using primary standard as type)
            if (transaction.response.primary_standard) {
              const type = transaction.response.primary_standard;
              transactionTypeMap[type] = (transactionTypeMap[type] || 0) + 1;
            }
          }
        });
        
        // Convert transaction types to array
        const transactionTypes = Object.entries(transactionTypeMap)
          .map(([name, count]) => ({ name, count }))
          .sort((a, b) => b.count - a.count);
        
        setReverseTransactionStats({
          totalTransactions: transactions.length,
          standardsAnalyzed: standardsCount,
          transactionTypes,
          anomaliesDetected: anomaliesCount
        });
        
        // Combine recent queries from both sources
        if (reverseTransactionQueries.length > 0) {
          setRecentQueries(prevQueries => {
            // Combine with any existing queries from useCase
            const allQueries = [...prevQueries, ...reverseTransactionQueries];
            // Sort by date and time (newest first)
            return allQueries
              .sort((a, b) => {
                const dateA = new Date(`${a.date} ${a.time}`);
                const dateB = new Date(`${b.date} ${b.time}`);
                return dateB.getTime() - dateA.getTime();
              })
              .slice(0, 10); // Keep only the 10 most recent
          });
        }
      } catch (error) {
        console.error('Error parsing ReverseTransaction history:', error);
      }
    }
    
    // We don't need to set recent queries from UseCase here as they're already handled in the UseCase history processing
  }, []);
  
  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Analytics Dashboard</h2>
      </div>

      {/* Use Case Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Use Case Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Total Conversations</div>
              <div className="text-3xl font-bold">{useCaseStats.totalConversations}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Assistant Messages</div>
              <div className="text-3xl font-bold">{useCaseStats.assistantMessages}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Avg Response Length</div>
              <div className="text-3xl font-bold">{useCaseStats.averageResponseLength} chars</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Avg Response Time</div>
              <div className="text-3xl font-bold">{useCaseStats.averageResponseTime > 0 ? `${useCaseStats.averageResponseTime}s` : 'N/A'}</div>
            </div>
          </div>
          
          {useCaseStats.topKeywords.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold ml-4 mb-4">Top Keywords</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={useCaseStats.topKeywords}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="word" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reverse Transaction Analytics */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Total Transactions Analyzed</div>
              <div className="text-3xl font-bold">{reverseTransactionStats.totalTransactions}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Standards Referenced</div>
              <div className="text-3xl font-bold">{reverseTransactionStats.standardsAnalyzed}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-green-800">Anomalies Detected</div>
              <div className="text-3xl font-bold">{reverseTransactionStats.anomaliesDetected}</div>
            </div>
          </div>
          
          {reverseTransactionStats.transactionTypes.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-4">Transaction Types Distribution</h3>
              <div className="flex flex-col md:flex-row items-center justify-center">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={reverseTransactionStats.transactionTypes}
                      cx="50%"
                      cy="50%"
                      labelLine={true}
                      label={({ name, percent }: { name: string, percent: number }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {reverseTransactionStats.transactionTypes.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Queries */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Queries</CardTitle>
        </CardHeader>
        <CardContent>
          {recentQueries.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-green-50">
                    <th className="p-3 text-left font-medium text-green-800">Date</th>
                    <th className="p-3 text-left font-medium text-green-800">Time</th>
                    <th className="p-3 text-left font-medium text-green-800">Query</th>
                    <th className="p-3 text-left font-medium text-green-800">Transaction Data</th>
                    <th className="p-3 text-left font-medium text-green-800">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {recentQueries.map((query, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="p-3">{query.date}</td>
                      <td className="p-3">{query.time}</td>
                      <td className="p-3">{query.content}</td>
                      <td className="p-3">{query.transactionData}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs ${query.type === 'useCase' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                          {query.type === 'useCase' ? 'Use Case' : 'Reverse Transaction'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center text-gray-500 py-4">No recent queries found</p>
          )}
        </CardContent>
      </Card>
      <ScrollToTop />
    </div>
  );
}