import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SendIcon, Upload, FileText, ChevronDown, Table, Calculator, Trash2 } from "lucide-react";
import { CustomModal } from "@/components/ui/custom-modal";
import ReactMarkdown from 'react-markdown';
import { ScrollToTop } from "../ScrollToTop";
import * as pdfjsLib from "pdfjs-dist";
import mammoth from 'mammoth';

// Set worker path for pdf.js
pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

// Financial calculation interface
interface FinancialCalculation {
  label: string;
  value: number;
}

// Journal entry interface
interface JournalEntry {
  debit?: string;
  credit?: string;
  amount: number;
}

// Ledger row interface for table display
interface LedgerRow {
  [key: string]: string | number;
}

// Amortizable amount table entry interface
interface AmortizableTableEntry {
  description: string;
  amount: number;
}

// Structured finance response interface
interface StructuredFinanceResponse {
  explanation: string;
  calculations?: FinancialCalculation[];
  journal_entries?: JournalEntry[];
  ledger_summary?: LedgerRow[];
  amortizable_amount_table?: AmortizableTableEntry[];
  sections?: {
    analysis?: string;
    variables?: string;
    calculations?: string;
    journal_entries?: string;
    explanation?: string;
  };
}

// Interface to represent message format with optional thinking field
interface Message {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  structuredResponse?: StructuredFinanceResponse;
  timestamp?: number;
}

export default function UseCaseSection() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your ISDB Islamic finance assistant. Ask me about any Islamic finance use case or scenario."
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [expandedThinking, setExpandedThinking] = useState<number[]>([]);
  const [expandedSections, setExpandedSections] = useState<{ [key: number]: string[] }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [clearModalOpen, setClearModalOpen] = useState(false);
  // New state for validation
  const [validationModalOpen, setValidationModalOpen] = useState(false);
  const [, setCurrentValidation] = useState<{ messageIndex: number, query: string, response: string } | null>(null);
  const [validatedMessages, setValidatedMessages] = useState<number[]>([]);
  const [, setValidationLoading] = useState(false);
  const [validationResult, setValidationResult] = useState<{ success: boolean, message: string, standard_type?: string } | null>(null);

  // Load chat history and pending state from localStorage when component mounts
  useEffect(() => {
    const savedMessages = localStorage.getItem('useCaseChatHistory');
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
    const pendingState = localStorage.getItem('useCasePendingState');
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
          localStorage.removeItem('useCasePendingState');
        }
      } catch (error) {
        console.error('Error parsing pending state:', error);
        localStorage.removeItem('useCasePendingState');
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    // Only save if we have more than the initial greeting message
    if (messages.length > 1) {
      localStorage.setItem('useCaseChatHistory', JSON.stringify(messages));
    }

    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  // Function to scroll to the bottom of the chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleThinking = (index: number) => {
    setExpandedThinking(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const toggleSection = (messageIndex: number, sectionName: string) => {
    setExpandedSections(prev => {
      const currentSections = prev[messageIndex] || [];
      return {
        ...prev,
        [messageIndex]: currentSections.includes(sectionName)
          ? currentSections.filter(s => s !== sectionName)
          : [...currentSections, sectionName]
      };
    });
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
          // Use a type assertion with a comment to explain why we're using 'any'
          // pdfjsLib types are complex and we're just extracting the 'str' property
          // Use type assertion for PDF.js text items which have complex types
          const pageText = text.items.map((item) => {
            // Check if the item has a 'str' property (TextItem) before accessing it
            return 'str' in item ? item.str : '';
          }).join(' ');
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

      setInput(content);
      console.log('File content loaded:', content);
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file. Please try again.');
    }
  };

  // Function to extract thinking process and structured data from response
  // Define a proper type for the API response data
  interface ApiResponse {
    response?: string;
    thinking_process?: string;
    explanation?: string;
    structured_response?: StructuredFinanceResponse;
    [key: string]: unknown;
  }

  const parseResponse = (responseData: ApiResponse): {
    thinking: string | undefined,
    answer: string,
    structuredResponse?: StructuredFinanceResponse
  } => {
    // Check if response is already structured
    if (responseData.structured_response) {
      // Handle different response types according to financial product type
      let formattedContent = "";
      const structResponse = responseData.structured_response;
      
      // For Murabaha responses, only show the section title in the main content
      // and put the explanation in the explanation section to avoid duplication
      if (structResponse.sections && 
          (responseData.response?.includes("MURABAHA FINANCING") || 
          (structResponse.sections.analysis && structResponse.sections.analysis.includes("Murabaha")))) {
        
        // Just include the title without duplicating the explanation
        formattedContent = "## ANALYSIS OF MURABAHA FINANCING";
      } 
      // For Musharaka responses
      else if (structResponse.sections && 
              (responseData.response?.includes("MUSHARAKA FINANCING") || 
              (structResponse.sections.analysis && structResponse.sections.analysis.includes("Musharaka")))) {
        
        // Just include the title without duplicating the explanation
        formattedContent = "## ANALYSIS OF MUSHARAKA FINANCING";
      }
      // For Ijarah responses
      else if (structResponse.sections && 
              (responseData.response?.includes("IJARAH MBT SCENARIO") || 
              (structResponse.sections.analysis && structResponse.sections.analysis.includes("Ijarah")))) {
        
        // Just include the title without duplicating the explanation
        formattedContent = "## ANALYSIS OF IJARAH MBT SCENARIO";
      }
      // For other responses, use the full formatted response
      else {
        formattedContent = responseData.response || "Response processed successfully.";
      }
      
      return {
        thinking: responseData.thinking_process,
        answer: formattedContent,
        structuredResponse: responseData.structured_response
      };
    }

    // Otherwise, check if there's a traditional text response with thinking tags
    const responseText = responseData.response || "Error processing your request";

    // Check if response contains <think> tags
    const thinkRegex = /<think>([\s\S]*?)<\/think>/;
    const thinkMatch = responseText.match(thinkRegex);

    let thinking: string | undefined;
    let answer: string = responseText;

    if (thinkMatch && thinkMatch[1]) {
      thinking = thinkMatch[1].trim();
      // Remove the thinking part from the response to get the clean answer
      answer = responseText.replace(thinkRegex, '').trim();
    }

    return { thinking, answer };
  };

  // Function to handle sending without updating state (for resuming pending requests)
  const handleSendWithoutStateUpdate = async (messageContent: string) => {
    try {
      // Save the pending state to localStorage
      localStorage.setItem('useCasePendingState', JSON.stringify({
        isPending: true,
        lastUserMessage: messageContent,
        timestamp: Date.now()
      }));

      const response = await fetch('http://127.0.0.1:5001/usecase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: messageContent
        }),
      });

      const data = await response.json();
      const parsedResponse = parseResponse(data);

      // Add assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: parsedResponse.answer,
        thinking: parsedResponse.thinking,
        structuredResponse: parsedResponse.structuredResponse,
        timestamp: Date.now()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Clear the pending state in localStorage
      localStorage.removeItem('useCasePendingState');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, there was an error processing your request. Please try again."
      }]);

      // Clear the pending state in localStorage
      localStorage.removeItem('useCasePendingState');
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
      // No need to reset fileContent as it's already reset in the main handleSend function
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !selectedFile) return;

    const contentToSend = input;
    console.log('Sending text:', contentToSend);

    // Add user message - preserve newlines in the displayed message
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
    setIsLoading(true);

    // Save the pending state to localStorage
    localStorage.setItem('useCasePendingState', JSON.stringify({
      isPending: true,
      lastUserMessage: contentToSend,
      timestamp: Date.now()
    }));

    try {
      const response = await fetch('http://127.0.0.1:5001/usecase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: contentToSend
        }),
      });

      const data = await response.json();
      const parsedResponse = parseResponse(data);

      // Add assistant message with timestamp
      setMessages(prev => [...prev, {
        role: "assistant",
        content: parsedResponse.answer,
        thinking: parsedResponse.thinking,
        structuredResponse: parsedResponse.structuredResponse,
        timestamp: Date.now()
      }]);

      // Clear the pending state in localStorage
      localStorage.removeItem('useCasePendingState');
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, there was an error processing your request. Please try again."
      }]);

      // Clear the pending state in localStorage
      localStorage.removeItem('useCasePendingState');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Render structured financial data sections
  const renderStructuredData = (message: Message, index: number) => {
    if (!message.structuredResponse) return null;

    const { calculations, journal_entries, ledger_summary, amortizable_amount_table, sections } = message.structuredResponse;
    const isExpanded = expandedSections[index] || [];

    // Check if this is a percentage-of-completion scenario for special handling
    const isPOCScenario = ledger_summary && ledger_summary.length > 0 &&
      (ledger_summary.some(row => row.Quarter && String(row.Quarter).startsWith('Q')) ||
        message.content.toLowerCase().includes('istisna') ||
        message.content.toLowerCase().includes('percentage of completion'));
    
    // Check if this is a structured response with detailed sections
    const hasDetailedSections = sections && Object.keys(sections).length > 0;
    
    // Standard background colors for different section types
    const sectionColors: Record<string, { bg: string, hover: string, text: string }> = {
      'explanation': { bg: 'bg-purple-50', hover: 'hover:bg-purple-100', text: 'text-purple-800' },
      'analysis': { bg: 'bg-indigo-50', hover: 'hover:bg-indigo-100', text: 'text-indigo-800' },
      'variables': { bg: 'bg-blue-50', hover: 'hover:bg-blue-100', text: 'text-blue-800' },
      'calculations': { bg: 'bg-green-50', hover: 'hover:bg-green-100', text: 'text-green-800' },
      'journal_entries': { bg: 'bg-amber-50', hover: 'hover:bg-amber-100', text: 'text-amber-800' }
    };
    
    // Section icons
    const sectionIcons: Record<string, React.ReactNode> = {
      'explanation': <FileText className="h-5 w-5 mr-2" />,
      'analysis': <FileText className="h-5 w-5 mr-2" />,
      'variables': <FileText className="h-5 w-5 mr-2" />,
      'calculations': <Calculator className="h-5 w-5 mr-2" />,
      'journal_entries': <Table className="h-5 w-5 mr-2" />
    };
    
    // Display names for sections
    const sectionDisplayNames: Record<string, string> = {
      'explanation': 'Additional Explanation',
      'analysis': 'Analysis',
      'variables': 'Extracted Variables',
      'calculations': 'Detailed Calculations',
      'journal_entries': 'Journal Entries'
    };

    return (
      <div className="space-y-4 mt-4">
        {/* Dynamic Sections from structured response */}
        {hasDetailedSections && (
          <>
            {/* Add the explanation as normal text if it exists in sections - MOVED TO DISPLAY FIRST */}
            {sections.explanation && (
              <div className="mb-4 p-4 bg-white rounded-lg border">
                <ReactMarkdown components={{
                  p: ({ children }) => {
                    return <p className="mb-3 whitespace-pre-line">{children}</p>;
                  }
                }}>
                  {sections.explanation}
                </ReactMarkdown>
              </div>
            )}
            
            {Object.entries(sections).map(([key, content]) => {
              // Skip empty content and don't create a collapsible section for explanation
              if (!content || key === 'explanation') return null;
              
              return (
                <div key={key} className="w-full border rounded-lg overflow-hidden bg-white">
                  <button
                    onClick={() => toggleSection(index, key)}
                    className={`flex items-center justify-between w-full p-3 ${sectionColors[key]?.bg || 'bg-gray-50'} ${sectionColors[key]?.text || 'text-gray-800'} ${sectionColors[key]?.hover || 'hover:bg-gray-100'} transition-colors`}
                  >
                    <div className="flex items-center">
                      {sectionIcons[key] || <FileText className="h-5 w-5 mr-2" />}
                      <span className="font-medium">{sectionDisplayNames[key] || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    </div>
                    <ChevronDown className={`h-5 w-5 transition-transform ${isExpanded.includes(key) ? 'rotate-180' : ''}`} />
                  </button>
                  <div className={`transition-all duration-300 ${isExpanded.includes(key) ? 'max-h-[500px] opacity-100 overflow-y-auto' : 'max-h-0 opacity-0 overflow-hidden'}`}>
                    <div className="p-4">
                      <ReactMarkdown components={{
                        // Preserve newlines in code blocks and paragraphs
                        code: ({ node, inline, className, children, ...props }) => {
                          return inline ? (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          ) : (
                            <pre className="whitespace-pre-wrap">
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                          );
                        },
                        p: ({ children }) => {
                          return <p className="mb-3 whitespace-pre-line">{children}</p>;
                        },
                        // Properly render tables
                        table: ({ children }) => {
                          return (
                            <div className="overflow-x-auto my-4">
                              <table className="min-w-full divide-y divide-gray-200">{children}</table>
                            </div>
                          );
                        },
                        thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
                        tbody: ({ children }) => <tbody className="divide-y divide-gray-200">{children}</tbody>,
                        tr: ({ children }) => <tr className="hover:bg-gray-50">{children}</tr>,
                        th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-medium text-gray-600">{children}</th>,
                        td: ({ children }) => <td className="px-3 py-2 text-sm">{children}</td>
                      }}>{content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              );
            })}
          </>
        )}
        
        {/* Standard Calculations Section - Only show if not already included in detailed sections */}
        {calculations && calculations.length > 0 && (!sections || !sections.calculations) && (
          <div className="w-full border rounded-lg overflow-hidden bg-white">
            <button
              onClick={() => toggleSection(index, 'calculations')}
              className="flex items-center justify-between w-full p-3 bg-blue-50 text-blue-800 hover:bg-blue-100 transition-colors"
            >
              <div className="flex items-center">
                <Calculator className="h-5 w-5 mr-2" />
                <span className="font-medium">Financial Calculations</span>
              </div>
              <ChevronDown className={`h-5 w-5 transition-transform ${isExpanded.includes('calculations') ? 'rotate-180' : ''}`} />
            </button>
            <div className={`transition-all duration-300 ${isExpanded.includes('calculations') ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
              <div className="p-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="p-3 font-medium">Description</th>
                      <th className="p-3 font-medium text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {calculations.map((calc, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="p-3">{calc.label}</td>
                        <td className="p-3 text-right font-medium">
                          {calc.label.toLowerCase().includes('completion')
                            ? `${calc.value}%`
                            : formatCurrency(calc.value)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Amortizable Amount Table Section - For Ijarah */}
        {amortizable_amount_table && amortizable_amount_table.length > 0 && (
          <div className="w-full border rounded-lg overflow-hidden bg-white">
            <button
              onClick={() => toggleSection(index, 'amortizable')}
              className="flex items-center justify-between w-full p-3 bg-amber-50 text-amber-800 hover:bg-amber-100 transition-colors"
            >
              <div className="flex items-center">
                <Calculator className="h-5 w-5 mr-2" />
                <span className="font-medium">Amortizable Amount Calculation</span>
              </div>
              <ChevronDown className={`h-5 w-5 transition-transform ${isExpanded.includes('amortizable') ? 'rotate-180' : ''}`} />
            </button>
            <div className={`transition-all duration-300 ${isExpanded.includes('amortizable') ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
              <div className="p-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="p-3 font-medium">Description</th>
                      <th className="p-3 font-medium text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {amortizable_amount_table.map((entry, i) => (
                      <tr key={i} className={`hover:bg-gray-50 ${entry.description.toLowerCase().includes('amortizable') ? 'font-semibold' : ''}`}>
                        <td className="p-3">{entry.description}</td>
                        <td className="p-3 text-right">{formatCurrency(entry.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Journal Entries Section - Only show if not already included in detailed sections */}
        {journal_entries && journal_entries.length > 0 && (!sections || !sections.journal_entries) && (
          <div className="w-full border rounded-lg overflow-hidden bg-white">
            <button
              onClick={() => toggleSection(index, 'journal')}
              className="flex items-center justify-between w-full p-3 bg-green-50 text-green-800 hover:bg-green-100 transition-colors"
            >
              <div className="flex items-center">
                <Table className="h-5 w-5 mr-2" />
                <span className="font-medium">Journal Entries</span>
              </div>
              <ChevronDown className={`h-5 w-5 transition-transform ${isExpanded.includes('journal') ? 'rotate-180' : ''}`} />
            </button>
            <div className={`transition-all duration-300 ${isExpanded.includes('journal') ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
              <div className="p-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="p-3 font-medium">Account</th>
                      <th className="p-3 font-medium text-right">Debit</th>
                      <th className="p-3 font-medium text-right">Credit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {journal_entries.map((entry, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="p-3">{entry.debit || entry.credit}</td>
                        <td className="p-3 text-right">{entry.debit ? formatCurrency(entry.amount) : ''}</td>
                        <td className="p-3 text-right">{entry.credit ? formatCurrency(entry.amount) : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Ledger Summary Section - Enhanced for Percentage-of-Completion */}
        {ledger_summary && ledger_summary.length > 0 && (
          <div className="w-full border rounded-lg overflow-hidden bg-white">
            <button
              onClick={() => toggleSection(index, 'ledger')}
              className="flex items-center justify-between w-full p-3 bg-purple-50 text-purple-800 hover:bg-purple-100 transition-colors"
            >
              <div className="flex items-center">
                <Table className="h-5 w-5 mr-2" />
                <span className="font-medium">
                  {isPOCScenario ? 'Percentage-of-Completion Ledger' : 'Ledger Summary'}
                </span>
              </div>
              <ChevronDown className={`h-5 w-5 transition-transform ${isExpanded.includes('ledger') ? 'rotate-180' : ''}`} />
            </button>
            <div className={`transition-all duration-300 ${isExpanded.includes('ledger') ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
              <div className="p-4 overflow-x-auto">
                {ledger_summary.length > 0 && (
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {Object.keys(ledger_summary[0]).map((key, i) => (
                          <th key={i} className="p-3 font-medium">{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {ledger_summary.map((row, i) => (
                        <tr key={i} className={`hover:bg-gray-50 ${row.Quarter === 'Total' ? 'font-semibold bg-gray-50' : ''}`}>
                          {Object.entries(row).map(([, value], j) => (
                            <td key={j} className="p-3">
                              {typeof value === 'number' ? formatCurrency(value) : value}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {/* Percentage-of-Completion Progress Visualization - Kept from original code */}
                {isPOCScenario && (
                  <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-3 text-gray-700">Project Progress Visualization</h4>
                    <div className="space-y-4">
                      {ledger_summary
                        .filter(row => {
                          // Handle both 'Quarter' and 'Stage' fields for different formats
                          const period = row.Quarter || row.Stage || '';
                          return (String(period).startsWith('Q') || String(period).startsWith('Stage')) &&
                            period !== 'Total';
                        })
                        .map((row, i) => {
                          // Handle both Quarter and Stage formats
                          const period = row.Quarter || row.Stage || '';
                          let percentage = 0;

                          if (String(period).startsWith('Q')) {
                            // For Quarter format: Q1=25%, Q2=50%, etc.
                            const quarterNum = Number(String(period).replace('Q', ''));
                            percentage = quarterNum * 25;
                          } else if (String(period).startsWith('Stage')) {
                            // For Stage format: Stage 1=33%, Stage 2=67%, Stage 3=100%
                            const stageNum = Number(String(period).replace('Stage ', ''));
                            const totalStages = ledger_summary.filter(r => String(r.Stage || '').startsWith('Stage')).length;
                            percentage = Math.round((stageNum / totalStages) * 100);
                          }
                          return (
                            <div key={i} className="bg-white p-3 rounded-lg border">
                              <div className="flex justify-between mb-1">
                                <span className="font-medium">{row.Quarter || row.Stage}</span>
                                <span className="text-purple-700">{percentage}% Complete</span>
                              </div>
                              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-purple-600 rounded-full"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                              <div className="flex justify-between mt-2 text-sm text-gray-500">
                                <span>Cost: {formatCurrency((row["Cost of Sales"] || row["Cost"]) as number)}</span>
                                <span>Revenue: {formatCurrency(row.Revenue as number)}</span>
                                <span>Profit: {formatCurrency(row.Profit as number)}</span>
                              </div>
                            </div>
                          );
                        })
                      }
                    </div>

                    {/* Summary Stats */}
                    {ledger_summary.find(row => row.Quarter === 'Total' || row.Stage === 'Total') && (
                      <div className="mt-6 border-t pt-4">
                        <h4 className="font-medium mb-3 text-gray-700">Project Summary</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {(() => {
                            const totals = ledger_summary.find(row => row.Quarter === 'Total' || row.Stage === 'Total')!;
                            return [
                              { label: 'Total Revenue', value: totals.Revenue as number, color: 'text-green-600' },
                              { label: 'Total Cost', value: (totals["Cost of Sales"] || totals["Cost"]) as number, color: 'text-red-600' },
                              { label: 'Total Profit', value: totals.Profit as number, color: 'text-blue-600' }
                            ].map((stat, i) => (
                              <div key={i} className="bg-white p-4 rounded-lg border shadow-sm">
                                <div className="text-sm font-medium text-gray-700">{stat.label}</div>
                                <div className={`text-xl font-bold ${stat.color}`}>{formatCurrency(stat.value)}</div>
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Function to handle validation of AI responses
  const handleValidateResponse = async (query: string, response: string, messageIndex: number) => {
    setValidationLoading(true);

    try {
      const validationResponse = await fetch('http://127.0.0.1:5001/usecase/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: query,
          response_text: response
        }),
      });

      const data = await validationResponse.json();

      // Update state with validation result
      setValidationResult(data);
      setValidationModalOpen(true);

      // Mark the message as validated if successful
      if (data.success) {
        setValidatedMessages(prev => [...prev, messageIndex]);
      }
    } catch (error) {
      console.error('Error validating response:', error);
      setValidationResult({
        success: false,
        message: "There was an error validating the response. Please try again."
      });
      setValidationModalOpen(true);
    } finally {
      setValidationLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold mb-6">Use Case Analysis</h2>

        {/* Clear history button */}
        {messages.length > 1 && (
          <div className="mb-4 flex justify-end">
            <Button
              variant="outline"
              className="text-sm text-red-700 hover:text-red-800 hover:bg-red-50"
              onClick={() => setClearModalOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear Chat History
            </Button>
          </div>
        )}
      </div>

      <Card className="flex-1 mb-4 overflow-hidden flex flex-col">
        <CardContent className="p-4 overflow-y-auto flex-1">
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div key={index} className="space-y-2">
                {/* Display thinking process if available */}
                {message.thinking && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] w-full">
                      <button
                        onClick={() => toggleThinking(index)}
                        className="flex items-center justify-between w-full p-2 bg-amber-50 text-amber-900 rounded-t-lg border border-amber-200 hover:bg-amber-100 transition-colors"
                      >
                        <span className="text-sm font-medium">Thinking Process</span>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform duration-200 ${expandedThinking.includes(index) ? 'rotate-180' : ''
                            }`}
                        />
                      </button>
                      <div
                        className={`overflow-hidden transition-[max-height,opacity] duration-300 ease-in-out ${expandedThinking.includes(index)
                          ? 'max-h-[500px] opacity-100'
                          : 'max-h-0 opacity-0'
                          }`}
                      >
                        <div className="p-4 bg-amber-50 text-amber-900 border border-t-0 border-amber-200 rounded-b-lg">
                          <ReactMarkdown components={{
                            // Make numbers bold in thinking process
                            text: ({ ...props }) => {
                              const text = props.children as string;
                              // Replace numbers with bold numbers
                              const formattedText = text.replace(/([0-9,.]+)/g, '**$1**');
                              return <ReactMarkdown>{formattedText}</ReactMarkdown>;
                            }
                          }}>{message.thinking}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${message.role === "user"
                      ? "bg-green-600 text-white"
                      : "bg-green-50 text-green-900"
                      } relative`}
                  >
                    {/* Add validation button for AI responses */}
                    {message.role === "assistant" && index > 0 && !validatedMessages.includes(index) && (
                      <button
                        onClick={() => {
                          // Find the preceding user message
                          const userMessageIndex = messages.slice(0, index).reverse()
                            .findIndex(msg => msg.role === "user");

                          if (userMessageIndex >= 0) {
                            const userMessage = messages[index - userMessageIndex - 1];
                            setCurrentValidation({
                              messageIndex: index,
                              query: userMessage.content,
                              response: message.content
                            });
                            handleValidateResponse(userMessage.content, message.content, index);
                          }
                        }}
                        className="absolute top-1 right-1 bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs py-1 px-2 rounded"
                        title="Validate this response as a good example"
                      >
                        Validate ✓
                      </button>
                    )}

                    {/* Show validation badge if message is validated */}
                    {message.role === "assistant" && validatedMessages.includes(index) && (
                      <div className="absolute top-1 right-1 bg-green-100 text-green-800 text-xs py-1 px-2 rounded flex items-center">
                        <span className="mr-1">✓</span> Validated
                      </div>
                    )}

                    <div className="markdown-content">
                      {message.role === "user" ? (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      ) : (
                        <ReactMarkdown
                          components={{
                            // Make numbers and key financial terms bold in response
                            p: ({ children }) => {
                              return <p className="mb-3">{children}</p>;
                            },
                            strong: ({ children }) => <span className="font-bold">{children}</span>,
                            // Properly render tables
                            table: ({ children }) => (
                              <div className="overflow-x-auto my-4">
                                <table className="min-w-full divide-y divide-gray-200">{children}</table>
                              </div>
                            ),
                            thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
                            tbody: ({ children }) => <tbody className="divide-y divide-gray-200">{children}</tbody>,
                            tr: ({ children }) => <tr className="hover:bg-gray-50">{children}</tr>,
                            th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-medium text-gray-600">{children}</th>,
                            td: ({ children }) => <td className="px-3 py-2 text-sm">{children}</td>,
                            text: ({ ...props }) => {
                              const text = props.children as string;
                              
                              // Process the text in stages to properly handle overlapping patterns
                              
                              // First, make key financial terms bold
                              const keyTerms = [
                                "Debit", "Credit", "Dr\\.", "Cr\\.",
                                "Right of Use Asset", "ROU Asset", "Deferred Ijarah Cost",
                                "Ijarah Liability", "Amortizable Amount", "Journal Entry", "Journal Entries",
                                "Murabaha Asset", "Murabaha Receivables", "Deferred Murabaha Profit",
                                "Work-in-Progress", "Istisna'a Revenue", "Istisna'a Receivable", "Parallel Istisna'a",
                                "Cost of Sales", "Prime Cost", "Terminal Value", "Purchase Option", 
                                "Percentage of Completion", "Quarterly Progress", "Incremental Revenue",
                                "Contract Value", "Total Cost", "Expected Profit", "Profit Margin"
                              ];
                              
                              let formattedText = text;
                              keyTerms.forEach(term => {
                                const regex = new RegExp(`\\b(${term})\\b`, 'gi');
                                formattedText = formattedText.replace(regex, '**$1**');
                              });
                              
                              // Then make numbers bold, but avoid double-bolding numbers in already bolded terms
                              formattedText = formattedText.replace(/(\$?[0-9,.]+%?)(?!\*\*)/g, '**$1**');
                              
                              return <>{formattedText}</>;
                            }
                          }}
                          remarkPlugins={[]}
                        >
                          {message.content}
                        </ReactMarkdown>
                      )}
                    </div>

                    {/* Render structured financial data if available */}
                    {message.role === "assistant" && message.structuredResponse &&
                      renderStructuredData(message, index)
                    }
                  </div>
                </div>
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
              placeholder="Ask about an Islamic finance use case or upload a file..."
              className="w-full pr-20 border-2 py-3 px-4 rounded-md resize-none overflow-auto whitespace-pre-wrap"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                // Dynamically adjust rows based on content
                const textarea = e.target;
                textarea.rows = 1; // Reset to 1 row
                const numberOfLines = textarea.value.split('\n').length;
                textarea.rows = Math.min(Math.max(numberOfLines, 1), 6); // Min 1 row, max 6 rows
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
            disabled={!input.trim() && !selectedFile}
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
          localStorage.removeItem('useCaseChatHistory');
          setMessages([
            {
              role: "assistant",
              content: "Hello! I'm your ISDB Islamic finance assistant. Ask me about any Islamic finance use case or scenario."
            }
          ]);
        }}
      />

      {/* Validation Result Modal */}
      <CustomModal
        isOpen={validationModalOpen}
        onClose={() => setValidationModalOpen(false)}
        title="Validation Result"
        description={validationResult ? validationResult.message : "No validation result available."}
        cancelText="Cancel"
        confirmText="Okay"
        onConfirm={() => setValidationModalOpen(false)}
        color="green" />
    </div>
  );
}