import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Sparkles } from 'lucide-react';

interface SuggestedQuestionsProps {
  onQuestionClick: (question: string) => void;
  isVisible: boolean;
}

const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ 
  onQuestionClick,
  isVisible 
}) => {
  const [questions, setQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch questions from the API
  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/suggested-questions');
      if (response.ok) {
        const data = await response.json();
        setQuestions(data);
      } else {
        console.error('Failed to fetch suggested questions');
        // Fallback questions
        setQuestions([
          "Show me the top 5 employees by hours worked",
          "Which locations have the most time entries?",
          "What are the most used activity codes?"
        ]);
      }
    } catch (error) {
      console.error('Error fetching suggested questions:', error);
      // Fallback questions
      setQuestions([
        "Show me the top 5 employees by hours worked",
        "Which locations have the most time entries?",
        "What are the most used activity codes?"
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch questions when component becomes visible
  useEffect(() => {
    if (isVisible) {
      fetchQuestions();
    }
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div className="px-4 py-4 border-t">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Suggested questions</span>
      </div>
      <div className="space-y-2">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading questions...</div>
        ) : questions.length > 0 ? (
          questions.map((question, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              className="w-full justify-start text-left h-auto py-2.5 px-3 text-sm font-normal hover:bg-accent hover:text-accent-foreground transition-colors"
              onClick={() => onQuestionClick(question)}
            >
              <span className="line-clamp-2">{question}</span>
            </Button>
          ))
        ) : (
          <div className="text-sm text-muted-foreground">No questions available</div>
        )}
      </div>
    </div>
  );
};

export default SuggestedQuestions;