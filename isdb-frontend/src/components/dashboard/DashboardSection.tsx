import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollToTop } from "../ScrollToTop";
import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { CustomModal } from "@/components/ui/custom-modal";
// Import html2pdf library
import html2pdf from 'html2pdf.js';

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
    sections?: {
      analysis?: string;
      variables?: string;
      calculations?: string;
      journal_entries?: string;
      explanation?: string;
    };
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

// Interface for query items in the dashboard
interface QueryItem {
  content: string;
  date: string;
  time: string;
  transactionData: string;
  type: 'useCase' | 'reverseTransaction';
  messageIndex?: number;
  originalQuery?: string;
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
  
  const [recentQueries, setRecentQueries] = useState<QueryItem[]>([]);
  const [allMessages, setAllMessages] = useState<{
    useCase: UseCaseMessage[];
    reverseTransaction: ReverseTransactionMessage[];
  }>({
    useCase: [],
    reverseTransaction: []
  });

  // State for download report modal
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<{
    messageIndex: number; 
    title: string;
    type: 'useCase' | 'reverseTransaction';
  } | null>(null);
  const [reportGenerating, setReportGenerating] = useState(false);

  // Load and process data from localStorage
  useEffect(() => {
    // Process UseCase chat history
    const useCaseHistory = localStorage.getItem('useCaseChatHistory');
    if (useCaseHistory) {
      try {
        const messages = JSON.parse(useCaseHistory) as UseCaseMessage[];
        
        // Store all messages for report generation
        setAllMessages(prev => ({...prev, useCase: messages}));
        
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
        // Process user messages to get user-assistant pairs
        // Skip the first message if it's a static welcome message
        const startIndex = messages[0]?.role === 'assistant' && !messages[0]?.content.includes('?') ? 1 : 0;
        
        // Group messages into conversations (every user message followed by assistant response)
        const conversations = [];
        let currentConversation = [];
        
        for (let i = startIndex; i < messages.length; i++) {
          currentConversation.push(messages[i]);
          // If we have a user message followed by an assistant message, that's a complete conversation
          if (currentConversation.length >= 2 && 
              currentConversation[currentConversation.length-2].role === 'user' && 
              currentConversation[currentConversation.length-1].role === 'assistant') {
            conversations.push([...currentConversation]);
            currentConversation = [];
          }
        }
        
        // If there's an incomplete conversation (just a user message without response), add it too
        if (currentConversation.length > 0) {
          conversations.push(currentConversation);
        }
        
        const useCaseQueries = conversations.map(conversation => {
          // Get the first user message in this conversation
          const userMsg = conversation.find(msg => msg.role === 'user');
          // Get the corresponding assistant response
          const assistantMsg = conversation.find(msg => msg.role === 'assistant');
          
          if (!userMsg) return null; // Skip if no user message found
          
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
          const timestamp = userMsg.timestamp ? new Date(userMsg.timestamp) : new Date();
          
          // Find the index of the assistant message in the original messages array
          const msgIndex = assistantMsg ? messages.findIndex(msg => 
            msg.role === 'assistant' && 
            msg.content === assistantMsg.content && 
            msg.timestamp === assistantMsg.timestamp
          ) : -1;
          
          return {
            content: userMsg.content.length > 50 ? userMsg.content.substring(0, 50) + '...' : userMsg.content,
            date: timestamp.toLocaleDateString(),
            time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            transactionData,
            type: 'useCase' as const,
            messageIndex: msgIndex,
            originalQuery: userMsg.content
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
          // Filter out any null values that might have been returned
          const validQueries = useCaseQueries.filter(query => query !== null) as QueryItem[];
          // Reset the queries state to only contain the most recent UseCase queries
          setRecentQueries(validQueries);
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
        
        // Store all messages for report generation
        setAllMessages(prev => ({...prev, reverseTransaction: messages}));
        
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
        // Process user messages to get user-assistant pairs
        // Skip the first message if it's a static welcome message
        const startIndex = messages[0]?.role === 'assistant' && !messages[0]?.content.includes('?') ? 1 : 0;
        
        // Group messages into conversations (every user message followed by assistant response)
        const conversations = [];
        let currentConversation = [];
        
        for (let i = startIndex; i < messages.length; i++) {
          currentConversation.push(messages[i]);
          // If we have a user message followed by an assistant message, that's a complete conversation
          if (currentConversation.length >= 2 && 
              currentConversation[currentConversation.length-2].role === 'user' && 
              currentConversation[currentConversation.length-1].role === 'assistant') {
            conversations.push([...currentConversation]);
            currentConversation = [];
          }
        }
        
        // If there's an incomplete conversation (just a user message without response), add it too
        if (currentConversation.length > 0) {
          conversations.push(currentConversation);
        }
        
        const reverseTransactionQueries = conversations.map(conversation => {
          // Get the first user message in this conversation
          const userMsg = conversation.find(msg => msg.role === 'user');
          // Get the corresponding assistant response
          const assistantMsg = conversation.find(msg => msg.role === 'assistant');
          
          if (!userMsg) return null; // Skip if no user message found
          
          let transactionData = 'N/A';
            
          // Extract transaction data - number of anomalies if available
          if (assistantMsg?.response?.anomalies) {
            transactionData = `${assistantMsg.response.anomalies.length} anomalies`;
          }
          
          // Format timestamp
          const timestamp = userMsg.timestamp ? new Date(userMsg.timestamp) : new Date();
          
          // Find the index of the assistant message in the original messages array
          const msgIndex = assistantMsg ? messages.findIndex(msg => 
            msg.role === 'assistant' && 
            msg.content === assistantMsg.content && 
            msg.timestamp === assistantMsg.timestamp
          ) : -1;
          
          return {
            content: userMsg.content.length > 50 ? userMsg.content.substring(0, 50) + '...' : userMsg.content,
            date: timestamp.toLocaleDateString(),
            time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            transactionData,
            type: 'reverseTransaction' as const,
            messageIndex: msgIndex,
            originalQuery: userMsg.content
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
          // Filter out any null values that might have been returned
          const validQueries = reverseTransactionQueries.filter(query => query !== null) as QueryItem[];
          setRecentQueries(prevQueries => {
            // Combine with any existing queries from useCase
            const allQueries = [...prevQueries, ...validQueries];
            
            // Create a map to deduplicate queries based on content
            const uniqueQueries = new Map();
            
            // Add each query to the map, using a truncated content as the key
            // This helps with deduplication when the same query appears with slight differences
            allQueries.forEach(query => {
              // Use the first 30 characters as the key for better deduplication
              const key = query.content.substring(0, 30);
              // Only update the map if this key doesn't exist or if the current query is newer
              if (!uniqueQueries.has(key) || 
                  new Date(`${query.date} ${query.time}`).getTime() > 
                  new Date(`${uniqueQueries.get(key).date} ${uniqueQueries.get(key).time}`).getTime()) {
                uniqueQueries.set(key, query);
              }
            });
            
            // Convert map values back to array and sort by date
            return Array.from(uniqueQueries.values())
              .sort((a, b) => {
                const dateA = new Date(`${a.date} ${a.time}`);
                const dateB = new Date(`${b.date} ${b.time}`);
                return dateB.getTime() - dateA.getTime();
              })
              .slice(0, 20); // Keep up to 20 recent queries
          });
        }
      } catch (error) {
        console.error('Error parsing ReverseTransaction history:', error);
      }
    }
  }, []);
  
  // Function to generate and download a report
  const downloadReport = async (messageIndex: number, type: 'useCase' | 'reverseTransaction') => {
    if (messageIndex < 0) {
      console.error("Invalid message index for report generation");
      return;
    }
    
    setReportGenerating(true);
    
    try {
      // Get the appropriate messages array based on type
      const messages = type === 'useCase' ? allMessages.useCase : allMessages.reverseTransaction;
      
      if (messageIndex >= messages.length) {
        console.error("Message index out of bounds for report generation");
        setReportGenerating(false);
        return;
      }
      
      // Get the assistant message and find the corresponding user question
      const assistantMessage = messages[messageIndex];
      if (assistantMessage.role !== 'assistant') {
        console.error("Selected message is not from assistant");
        setReportGenerating(false);
        return;
      }
      
      // Find the user message that preceded this assistant message
      let userMessage;
      for (let i = messageIndex - 1; i >= 0; i--) {
        if (messages[i].role === 'user') {
          userMessage = messages[i];
          break;
        }
      }
      
      if (!userMessage) {
        console.error("Could not find corresponding user message");
        setReportGenerating(false);
        return;
      }
      
      // Format date for the report
      const date = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });

      // Determine the title for the report based on content
      let title = type === 'useCase' ? "Islamic Finance Analysis Report" : "Transaction Analysis Report";
      
      if (type === 'useCase') {
        const useCaseMsg = assistantMessage as UseCaseMessage;
        
        // Try to extract a more specific title from the content
        if (useCaseMsg.structuredResponse?.sections?.analysis) {
          const analysisText = useCaseMsg.structuredResponse.sections.analysis;
          if (analysisText.includes("MURABAHA")) {
            title = "Murabaha Financing Analysis Report";
          } else if (analysisText.includes("IJARAH")) {
            title = "Ijarah MBT Analysis Report";
          } else if (analysisText.includes("ISTISNA")) {
            title = "Istisna'a Contract Analysis Report";
          } else if (analysisText.includes("SALAM")) {
            title = "Salam Contract Analysis Report";
          } else if (analysisText.includes("MUSHARAKA")) {
            title = "Musharaka Financing Analysis Report";
          } else if (analysisText.includes("SUKUK")) {
            title = "Sukuk Analysis Report";
          }
        } else if (useCaseMsg.content) {
          // Try to extract title from content
          const content = useCaseMsg.content.toLowerCase();
          if (content.includes("murabaha")) {
            title = "Murabaha Financing Analysis Report";
          } else if (content.includes("ijarah")) {
            title = "Ijarah MBT Analysis Report";
          } else if (content.includes("istisna")) {
            title = "Istisna'a Contract Analysis Report";
          } else if (content.includes("salam")) {
            title = "Salam Contract Analysis Report";
          } else if (content.includes("musharaka")) {
            title = "Musharaka Financing Analysis Report";
          } else if (content.includes("sukuk")) {
            title = "Sukuk Analysis Report";
          }
        }
      } else {
        // For reverse transaction, use the primary standard as the title
        const reverseMsg = assistantMessage as ReverseTransactionMessage;
        if (reverseMsg.response?.primary_standard) {
          title = `${reverseMsg.response.primary_standard} Analysis Report`;
        }
      }

      // Create a complete HTML document with styling
      let reportContent = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>${title}</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
            }
            .header {
              text-align: center;
              margin-bottom: 30px;
              border-bottom: 2px solid #4f946c;
              padding-bottom: 10px;
            }
            .header h1 {
              color: #2d6a4f;
              margin-bottom: 5px;
            }
            .header p {
              color: #666;
              margin-top: 0;
            }
            .section {
              margin-bottom: 25px;
              page-break-inside: avoid;
            }
            .section-title {
              background-color: #edf7f0;
              color: #2d6a4f;
              padding: 8px 15px;
              border-radius: 5px;
              margin-bottom: 15px;
              font-weight: bold;
            }
            .scenario {
              background-color: #f8f9fa;
              padding: 15px;
              border-radius: 5px;
              border-left: 4px solid #4f946c;
              margin-bottom: 20px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 15px 0;
              page-break-inside: avoid;
            }
            table, th, td {
              border: 1px solid #ddd;
            }
            th {
              background-color: #f2f2f2;
              padding: 10px;
              text-align: left;
            }
            td {
              padding: 8px 10px;
            }
            .footer {
              margin-top: 40px;
              text-align: center;
              font-size: 12px;
              color: #888;
              border-top: 1px solid #ddd;
              padding-top: 15px;
            }
            .analysis-content {
              margin-bottom: 20px;
            }
            .calculations table {
              width: 100%;
            }
            .journal-entries table tr:nth-child(odd) {
              background-color: #f9f9f9;
            }
            .thinking {
              background-color: #fffaed;
              padding: 15px;
              border-radius: 5px;
              border-left: 4px solid #f0c040;
              margin-bottom: 20px;
              font-style: italic;
              page-break-inside: avoid;
            }
            .anomalies {
              background-color: #feebeb;
              padding: 15px;
              border-radius: 5px;
              border-left: 4px solid #e53e3e;
              margin-bottom: 20px;
              page-break-inside: avoid;
            }
            .standards {
              background-color: #ebf8ff;
              padding: 15px;
              border-radius: 5px;
              border-left: 4px solid #3182ce;
              margin-bottom: 20px;
              page-break-inside: avoid;
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>${title}</h1>
            <p>Generated on ${date}</p>
          </div>

          <div class="section">
            <div class="section-title">SCENARIO</div>
            <div class="scenario">
              ${userMessage.content.replace(/\n/g, '<br>')}
            </div>
          </div>
      `;

      // Add content based on the message type
      if (type === 'useCase') {
        const useCaseMsg = assistantMessage as UseCaseMessage;
        
        // Add analysis section
        reportContent += `
          <div class="section">
            <div class="section-title">ANALYSIS</div>
            <div class="analysis-content">
              ${useCaseMsg.content.replace(/\n/g, '<br>')}
            </div>
          </div>
        `;
        
        // Add structured response sections if available
        if (useCaseMsg.structuredResponse) {
          const { sections, calculations, journal_entries, ledger_summary, amortizable_amount_table } = useCaseMsg.structuredResponse;
          
          // Add sections content if available
          if (sections) {
            if (sections.variables) {
              reportContent += `
                <div class="section">
                  <div class="section-title">EXTRACTED VARIABLES</div>
                  <div class="analysis-content">
                    ${sections.variables.replace(/\n/g, '<br>')}
                  </div>
                </div>
              `;
            }
            
            if (sections.calculations) {
              reportContent += `
                <div class="section">
                  <div class="section-title">CALCULATIONS</div>
                  <div class="analysis-content">
                    ${sections.calculations.replace(/\n/g, '<br>')}
                  </div>
                </div>
              `;
            }
            
            if (sections.journal_entries) {
              reportContent += `
                <div class="section">
                  <div class="section-title">JOURNAL ENTRIES</div>
                  <div class="analysis-content">
                    ${sections.journal_entries.replace(/\n/g, '<br>')}
                  </div>
                </div>
              `;
            }
            
            if (sections.explanation) {
              reportContent += `
                <div class="section">
                  <div class="section-title">EXPLANATION</div>
                  <div class="analysis-content">
                    ${sections.explanation.replace(/\n/g, '<br>')}
                  </div>
                </div>
              `;
            }
          }
          
          // Add calculations as a table if not already included in sections
          if (calculations && calculations.length > 0 && !sections?.calculations) {
            reportContent += `
              <div class="section">
                <div class="section-title">FINANCIAL CALCULATIONS</div>
                <div class="calculations">
                  <table>
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${calculations.map(calc => `
                        <tr>
                          <td>${calc.label}</td>
                          <td>${calc.label.toLowerCase().includes('completion')
                            ? `${calc.value}%`
                            : new Intl.NumberFormat('en-US', {
                                style: 'currency',
                                currency: 'USD'
                              }).format(calc.value)
                            }
                          </td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }
          
          // Add amortizable amount table if available
          if (amortizable_amount_table && amortizable_amount_table.length > 0) {
            reportContent += `
              <div class="section">
                <div class="section-title">AMORTIZABLE AMOUNT CALCULATION</div>
                <div class="calculations">
                  <table>
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${amortizable_amount_table.map(entry => `
                        <tr>
                          <td>${entry.description}</td>
                          <td>${new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD'
                          }).format(entry.amount)}</td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }
          
          // Add journal entries if not already included in sections
          if (journal_entries && journal_entries.length > 0 && !sections?.journal_entries) {
            reportContent += `
              <div class="section">
                <div class="section-title">JOURNAL ENTRIES</div>
                <div class="journal-entries">
                  <table>
                    <thead>
                      <tr>
                        <th>Account</th>
                        <th>Debit</th>
                        <th>Credit</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${journal_entries.map(entry => `
                        <tr>
                          <td>${entry.debit || entry.credit}</td>
                          <td>${entry.debit ? new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD'
                          }).format(entry.amount) : ''}</td>
                          <td>${entry.credit ? new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'USD'
                          }).format(entry.amount) : ''}</td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }
          
          // Add ledger summary table if available
          if (ledger_summary && ledger_summary.length > 0) {
            const headers = Object.keys(ledger_summary[0]);
            
            reportContent += `
              <div class="section">
                <div class="section-title">LEDGER SUMMARY</div>
                <div class="journal-entries">
                  <table>
                    <thead>
                      <tr>
                        ${headers.map(header => `<th>${header}</th>`).join('')}
                      </tr>
                    </thead>
                    <tbody>
                      ${ledger_summary.map(row => `
                        <tr>
                          ${headers.map(key => `
                            <td>${typeof row[key] === 'number' 
                              ? new Intl.NumberFormat('en-US', {
                                  style: 'currency',
                                  currency: 'USD'
                                }).format(row[key] as number)
                              : row[key]}
                            </td>
                          `).join('')}
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }
        }
        
        // Add thinking process if available
        if (useCaseMsg.thinking) {
          reportContent += `
            <div class="section">
              <div class="section-title">THINKING PROCESS</div>
              <div class="thinking">
                ${useCaseMsg.thinking.replace(/\n/g, '<br>')}
              </div>
            </div>
          `;
        }
      } else {
        // Handle Reverse Transaction report
        const reverseMsg = assistantMessage as ReverseTransactionMessage;
        
        // Add main content
        reportContent += `
          <div class="section">
            <div class="section-title">ANALYSIS</div>
            <div class="analysis-content">
              ${reverseMsg.content.replace(/\n/g, '<br>')}
            </div>
          </div>
        `;
        
        // Add structured response sections if available
        if (reverseMsg.response) {
          // Add anomalies if present
          if (reverseMsg.response.anomalies && reverseMsg.response.anomalies.length > 0) {
            reportContent += `
              <div class="section">
                <div class="section-title">ANOMALIES DETECTED</div>
                <div class="anomalies">
                  <ul>
                    ${reverseMsg.response.anomalies.map(anomaly => `
                      <li>${anomaly}</li>
                    `).join('')}
                  </ul>
                </div>
              </div>
            `;
          }
          
          // Add applicable standards
          if (reverseMsg.response.applicable_standards && reverseMsg.response.applicable_standards.length > 0) {
            reportContent += `
              <div class="section">
                <div class="section-title">APPLICABLE STANDARDS</div>
                <div class="standards">
                  <p><strong>Primary Standard:</strong> ${reverseMsg.response.primary_standard}</p>
                  <p><strong>Primary Sharia Standard:</strong> ${reverseMsg.response.primary_sharia_standard}</p>
                  
                  <h4>All Standards with Weight:</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Standard</th>
                        <th>Weight</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${reverseMsg.response.applicable_standards.map(standard => `
                        <tr>
                          <td>${standard.standard}</td>
                          <td>${standard.weight}%</td>
                          <td>${standard.reason}</td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }
          
          // Add thinking process
          if (reverseMsg.response.thinking_process && reverseMsg.response.thinking_process.length > 0) {
            reportContent += `
              <div class="section">
                <div class="section-title">THINKING PROCESS</div>
                <div class="thinking">
                  <ul>
                    ${reverseMsg.response.thinking_process.map(step => `
                      <li>${step}</li>
                    `).join('')}
                  </ul>
                </div>
              </div>
            `;
          }
        }
      }

      // Add footer
      reportContent += `
          <div class="footer">
            <p>Generated by ISDB Finance Assistant</p>
            <p>This report is for educational and informational purposes only.</p>
          </div>
        </body>
        </html>
      `;
      
      // Create a container element that will be converted to PDF
      const element = document.createElement('div');
      element.innerHTML = reportContent;
      document.body.appendChild(element);
      
      // Configure options for html2pdf
      const options = {
        margin: [10, 10, 10, 10], // [top, left, bottom, right] or [vertical, horizontal]
        filename: `${title.replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      
      // Generate PDF
      html2pdf()
        .from(element)
        .set(options)
        .save()
        .then(() => {
          // Cleanup
          document.body.removeChild(element);
          setReportModalOpen(false);
          setReportGenerating(false);
        })
        .catch((error) => {
          console.error('Error generating PDF:', error);
          setReportGenerating(false);
        });
    } catch (error) {
      console.error('Error generating report:', error);
      setReportGenerating(false);
    }
  };

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
                    <th className="p-3 text-left font-medium text-green-800">Actions</th>
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
                      <td className="p-3">
                        {query.messageIndex && query.messageIndex >= 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-sm text-blue-700 hover:text-blue-800 hover:bg-blue-50 flex items-center gap-1"
                            onClick={() => {
                              if (query.messageIndex !== undefined && query.messageIndex >= 0) {
                                setSelectedReport({
                                  messageIndex: query.messageIndex,
                                  title: query.content.length > 30 ? query.content.substring(0, 30) + '...' : query.content,
                                  type: query.type
                                });
                                setReportModalOpen(true);
                              }
                            }}
                          >
                            <Download className="h-3 w-3" />
                            Report
                          </Button>
                        )}
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
      
      {/* Report Generation Modal */}
      <CustomModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        title="Generate Full Report"
        description={`Do you want to generate a detailed report for "${selectedReport?.title}"? This will create a downloadable PDF file with all analysis and financial data.`}
        cancelText="Cancel"
        confirmText={reportGenerating ? "Generating..." : "Download Report"}
        onConfirm={() => {
          if (selectedReport) {
            downloadReport(selectedReport.messageIndex, selectedReport.type);
          }
        }}
        color="green"
      />
    </div>
  );
}