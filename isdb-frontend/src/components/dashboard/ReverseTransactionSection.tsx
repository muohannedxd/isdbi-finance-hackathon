import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SendIcon, Upload, FileText, ChevronDown, Trash2 } from "lucide-react";
import { CustomModal } from "@/components/ui/custom-modal";
import { ScrollToTop } from "../ScrollToTop";
import * as pdfjsLib from "pdfjs-dist";
import mammoth from "mammoth";

// Set worker path for pdf.js
pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

interface Standard {
  standard: string;
  reason: string;
  weight: number;
}

interface TransactionResponse {
  applicable_standards: Standard[];
  primary_standard: string;
  primary_sharia_standard: string;
  detailed_justification: string;
  thinking_process: string[];
  anomalies: string[];
}

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: TransactionResponse;
  timestamp?: number;
}

export default function ReverseTransactionSection() {
  const [input, setInput] = useState("");
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Please describe a financial transaction, and I'll analyze it from an Islamic finance perspective."
    }
  ]);

  // Load chat history and pending state from localStorage when component mounts
  useEffect(() => {
    const savedMessages = localStorage.getItem('reverseTransactionChatHistory');
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        if (Array.isArray(parsedMessages) && parsedMessages.length > 0) {
          setMessages(parsedMessages);
        }
      } catch (error) {
        console.error('Error parsing saved chat history:', error);
      }
    }
    
    // Check if there's a pending request
    const pendingState = localStorage.getItem('reverseTransactionPendingState');
    if (pendingState) {
      try {
        const { isPending, lastUserMessage } = JSON.parse(pendingState);
        if (isPending) {
          setIsLoading(true);
          // Re-send the last user message to continue the pending request
          if (lastUserMessage) {
            handleSendWithoutStateUpdate(lastUserMessage);
          }
        } else {
          // Clear the pending state if it's not pending
          localStorage.removeItem('reverseTransactionPendingState');
        }
      } catch (error) {
        console.error('Error parsing pending state:', error);
        localStorage.removeItem('reverseTransactionPendingState');
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    // Only save if we have more than the initial greeting message
    if (messages.length > 1) {
      localStorage.setItem('reverseTransactionChatHistory', JSON.stringify(messages));
    }
    
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);
  
  // Function to scroll to the bottom of the chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [expandedThinking, setExpandedThinking] = useState<number[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [clearModalOpen, setClearModalOpen] = useState(false);

  const toggleThinking = (index: number) => {
    setExpandedThinking(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    try {
      let content = '';

      if (file.type === 'application/pdf') {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        const numPages = pdf.numPages;
        const textContent = [];

        for (let i = 1; i <= numPages; i++) {
          const page = await pdf.getPage(i);
          const text = await page.getTextContent();
          // Use a simpler approach to avoid TypeScript errors with pdfjsLib types
          const pageText = text.items
            .filter((item: any) => typeof item === 'object' && item !== null && 'str' in item)
            .map((item: any) => item.str as string)
            .join(' ');
          textContent.push(pageText);
        }

        content = textContent.join('\n');
      } else if (file.type === 'application/msword' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        content = result.value;
      } else {
        // For text files
        content = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.onerror = (e) => reject(e);
          reader.readAsText(file);
        });
      }

      setInput(content); // Set the actual content in the input
      setFileContent(content);
      console.log('File content loaded:', content);
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file. Please try again.');
    }
  };

  // Function to handle sending without updating state (for resuming pending requests)
  const handleSendWithoutStateUpdate = async (messageContent: string) => {
    try {
      // Save the pending state to localStorage
      localStorage.setItem('reverseTransactionPendingState', JSON.stringify({
        isPending: true,
        lastUserMessage: messageContent,
        timestamp: Date.now()
      }));

      const response = await fetch('http://127.0.0.1:5002/reversetransaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: messageContent
        }),
      });

      const data: TransactionResponse = await response.json();

      // Add assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: data.detailed_justification,
        response: data,
        timestamp: Date.now()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Clear the pending state in localStorage
      localStorage.removeItem('reverseTransactionPendingState');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, there was an error analyzing your transaction. Please try again."
      }]);
      
      // Clear the pending state in localStorage
      localStorage.removeItem('reverseTransactionPendingState');
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !fileContent) return;

    const contentToSend = fileContent || input;
    console.log('Sending content:', contentToSend);

    // Add user message with timestamp
    const userMessage: Message = { 
      role: "user", 
      content: input,
      timestamp: Date.now() 
    };
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input and reset textarea height
    setInput("");
    // Reset textarea to single row after sending
    const textareaElement = document.querySelector('textarea');
    if (textareaElement) {
      textareaElement.rows = 1;
    }
    
    setSelectedFile(null);
    setFileContent(null);
    setIsLoading(true);
    
    // Save the pending state to localStorage
    localStorage.setItem('reverseTransactionPendingState', JSON.stringify({
      isPending: true,
      lastUserMessage: contentToSend,
      timestamp: Date.now()
    }));

    try {
      const response = await fetch('http://127.0.0.1:5002/reversetransaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: contentToSend
        }),
      });

      const data: TransactionResponse = await response.json();

      // Add assistant message with the structured response and timestamp
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.detailed_justification,
        response: data,
        timestamp: Date.now()
      }]);
      
      // Clear the pending state in localStorage
      localStorage.removeItem('reverseTransactionPendingState');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, there was an error analyzing your transaction. Please try again."
      }]);
      
      // Clear the pending state in localStorage
      localStorage.removeItem('reverseTransactionPendingState');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter") {
      if (e.shiftKey) {
        // Allow new line when Shift+Enter is pressed
        return;
      }
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold mb-6">Reverse Transaction Analysis</h2>
        
        {/* Clear history button */}
        {messages.length > 1 && (
          <div className="mb-4 flex justify-end">
            <Button 
              variant="outline" 
              className="text-sm text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={() => setClearModalOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear Chat History
            </Button>
          </div>
        )}
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>About Reverse Transaction Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground pl-4 pb-4">
            This tool analyzes financial transactions from an Islamic finance perspective. Describe any conventional
            financial transaction, and it will provide Shariah-compliant alternatives and insights according to
            Islamic finance principles.
          </p>
        </CardContent>
      </Card>

      <Card className="flex-1 mb-4 overflow-hidden flex flex-col">
        <CardContent className="p-4 overflow-y-auto flex-1">
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div key={index} className="space-y-4">
                <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-lg p-4 ${message.role === "user" ? "bg-green-600 text-white" : "bg-green-50 text-green-900"
                    }`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                </div>

                {message.response && (
                  <>
                    {/* Anomalies Section - Moved to top */}
                    {message.response.anomalies.length > 0 && (
                      <div className="flex justify-start">
                        <div className="max-w-[80%] w-full">
                          <div className="p-4 bg-red-50 text-red-900 rounded-lg border border-red-200">
                            <h3 className="font-semibold mb-2">Anomalies Detected</h3>
                            <ul className="list-disc pl-4">
                              {message.response.anomalies.map((anomaly, i) => (
                                <li key={i}>{anomaly}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Standards Section */}
                    <div className="flex justify-start">
                      <div className="max-w-[80%] w-full space-y-2">
                        <div className="p-4 bg-blue-50 text-blue-900 rounded-lg">
                          <h3 className="font-semibold mb-2">
                            {message.response.anomalies.length > 0 ? 'Potential ' : ''}
                            Applicable Standards
                          </h3>
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="font-medium">Primary Standard:</span>
                              <span className="bg-blue-100 px-2 py-1 rounded">{message.response.primary_standard}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="font-medium">Primary Sharia Standard:</span>
                              <span className="bg-blue-100 px-2 py-1 rounded">{message.response.primary_sharia_standard}</span>
                            </div>

                            {/* Standards with weights */}
                            <div className="mt-4">
                              <h4 className="font-medium mb-2">All Applicable Standards:</h4>
                              <div className="space-y-2">
                                {message.response.applicable_standards.map((standard, i) => (
                                  <div key={i} className="flex justify-between items-center bg-blue-100/50 p-2 rounded">
                                    <span>{standard.standard}</span>
                                    <div className="flex items-center gap-2">
                                      <span className="text-sm text-blue-700">Weight: {standard.weight}%</span>
                                      <div className="w-24 h-2 bg-blue-200 rounded-full overflow-hidden">
                                        <div
                                          className="h-full bg-blue-600 rounded-full"
                                          style={{ width: `${standard.weight}%` }}
                                        />
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Thinking Process */}
                        <button
                          onClick={() => toggleThinking(index)}
                          className="flex items-center justify-between w-full p-2 bg-amber-50 text-amber-900 rounded-lg border border-amber-200 hover:bg-amber-100 transition-colors"
                        >
                          <span className="text-sm font-medium">View Thinking Process</span>
                          <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${expandedThinking.includes(index) ? 'rotate-180' : ''
                            }`} />
                        </button>

                        <div className={`overflow-hidden transition-[max-height,opacity] duration-300 ease-in-out ${expandedThinking.includes(index) ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
                          }`}>
                          <div className="p-4 bg-amber-50 text-amber-900 border border-amber-200 rounded-lg mt-2">
                            <ul className="list-disc pl-4 space-y-1">
                              {message.response.thinking_process.map((step, i) => (
                                <li key={i}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        </div>


                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg p-4 bg-green-50 text-green-900">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce [animation-delay:0.2s]"></div>
                    <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce [animation-delay:0.4s]"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>
      <div className="relative flex items-center justify-center">
        <div className="flex gap-2 w-full">
          <div className="flex-1 relative">
            <textarea
              placeholder="Describe a financial transaction or upload a file..."
              className="w-full pr-20 border-2 py-3 px-4 rounded-md resize-none overflow-auto whitespace-pre-wrap"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                const textarea = e.target;
                textarea.rows = 1;
                const numberOfLines = textarea.value.split('\n').length;
                textarea.rows = Math.min(Math.max(numberOfLines, 1), 6); // Increased to 6 rows max
              }}
              onPaste={(e) => {
                // Handle paste event to preserve newlines
                e.preventDefault();
                const pastedText = e.clipboardData.getData('text');
                setInput(prev => prev + pastedText);
                
                // Adjust rows after paste
                setTimeout(() => {
                  const textarea = e.target as HTMLTextAreaElement;
                  const numberOfLines = textarea.value.split('\n').length;
                  textarea.rows = Math.min(Math.max(numberOfLines, 1), 6);
                }, 0);
              }}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={1}
            />
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".txt,.doc,.docx,.pdf"
              className="hidden"
            />
            <div className="absolute right-1 top-1/2 -translate-y-1/2 flex gap-2">
              {selectedFile && (
                <div className="flex items-center gap-1 px-2 py-1 bg-green-50 rounded-md text-sm text-green-800">
                  <FileText size={14} />
                  <span className="max-w-[100px] truncate">{selectedFile.name}</span>
                </div>
              )}
              <Button
                className="bg-green-100 hover:bg-green-200"
                size="icon"
                variant="ghost"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                <Upload className="h-4 w-4 text-green-800" />
              </Button>
            </div>
          </div>
          <Button
            className="bg-green-600 hover:bg-green-700 px-8 min-h-[48px]"
            onClick={handleSend}
            disabled={!input.trim() && !fileContent}
          >
            <SendIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <ScrollToTop />
      
      {/* Clear Chat History Modal */}
      <CustomModal
        isOpen={clearModalOpen}
        onClose={() => setClearModalOpen(false)}
        title="Clear Chat History"
        description="Are you sure you want to clear your chat history? This action cannot be undone."
        confirmText="Clear History"
        cancelText="Cancel"
        onConfirm={() => {
          localStorage.removeItem('reverseTransactionChatHistory');
          setMessages([
            {
              role: "assistant",
              content: "Please describe a financial transaction, and I'll analyze it from an Islamic finance perspective."
            }
          ]);
        }}
      />
    </div>
  );
}