import { Link } from 'react-router-dom';
import { Logo } from '@/components/shared/Logo';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  Upload,
  HelpCircle,
  CheckCircle,
  ArrowRight,
} from 'lucide-react';

const features = [
  {
    icon: FileText,
    title: 'Multi-Format Support',
    description:
      'Upload PDFs, Word documents, Excel files, and images. DocChat processes them seamlessly.',
  },
  {
    icon: MessageSquare,
    title: 'Natural Language Queries',
    description:
      'Ask questions in plain English. No complex query syntax needed — just chat naturally.',
  },
  {
    icon: Sparkles,
    title: 'AI-Powered Answers',
    description:
      'Get accurate, contextual answers powered by advanced retrieval-augmented generation.',
  },
  {
    icon: ShieldCheck,
    title: 'Quality Assurance',
    description:
      'Built-in LLM-as-a-judge evaluation ensures answer quality, relevance, and faithfulness.',
  },
];

const steps = [
  {
    icon: Upload,
    number: 1,
    title: 'Upload',
    description: 'Drop your documents into DocChat - PDFs, DOCX, XLSX, and images.',
  },
  {
    icon: HelpCircle,
    number: 2,
    title: 'Ask',
    description: 'Type your question in natural language, just like chatting with a colleague.',
  },
  {
    icon: CheckCircle,
    number: 3,
    title: 'Get Answers',
    description: 'Receive accurate, sourced answers with references back to your documents.',
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Logo size="md" />
          <div className="flex items-center gap-6">
            <a
              href="#features"
              className="hidden text-sm text-muted-foreground transition-colors hover:text-foreground sm:inline"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="hidden text-sm text-muted-foreground transition-colors hover:text-foreground sm:inline"
            >
              How it Works
            </a>
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/login?tab=register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="bg-gradient-to-br from-primary/5 via-background to-primary/10">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 md:grid-cols-2 md:py-32">
          <div className="space-y-6">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              Chat with your{' '}
              <span className="text-primary">documents</span>
            </h1>
            <p className="max-w-md text-lg text-muted-foreground">
              Upload any document and get instant, AI-powered answers. DocChat understands your
              files so you don't have to read them cover to cover.
            </p>
            <Link to="/login?tab=register">
              <Button size="lg" className="mt-2 gap-2">
                Get Started Free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Chat mockup */}
          <Card className="mx-auto w-full max-w-md border shadow-xl">
            <CardContent className="space-y-4 p-6">
              {/* User message */}
              <div className="flex justify-end">
                <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  What are the key findings in Q4?
                </div>
              </div>
              {/* AI response */}
              <div className="space-y-2">
                <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-2.5 text-sm">
                  Based on the Q4 report, revenue grew 23% YoY driven by strong enterprise
                  adoption. Customer retention improved to 94%.
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline" className="text-xs">
                    Q4-Report.pdf, p.12
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    Q4-Report.pdf, p.28
                  </Badge>
                </div>
              </div>
              {/* Another user message */}
              <div className="flex justify-end">
                <div className="rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  How does that compare to Q3?
                </div>
              </div>
              {/* Another AI response */}
              <div className="space-y-2">
                <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-2.5 text-sm">
                  Q3 revenue growth was 18% YoY, so Q4 represents a 5-point acceleration.
                  Retention was flat at 93%.
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline" className="text-xs">
                    Q3-Report.pdf, p.8
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Everything you need to chat with your documents
            </h2>
            <p className="mt-3 text-muted-foreground">
              Powerful features that make document interaction effortless.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2">
            {features.map((feature) => (
              <Card key={feature.title} className="border bg-card">
                <CardContent className="flex gap-4 p-6">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{feature.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="border-t bg-muted/30 py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">How it works</h2>
            <p className="mt-3 text-muted-foreground">
              Three simple steps to get answers from your documents.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-3">
            {steps.map((step, i) => (
              <div key={step.title} className="relative text-center">
                {/* Connecting line */}
                {i < steps.length - 1 && (
                  <div className="absolute right-0 top-6 hidden h-0.5 w-full translate-x-1/2 bg-border sm:block" />
                )}
                <div className="relative mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                  {step.number}
                </div>
                <h3 className="text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <Logo size="sm" />
            <span className="text-sm text-muted-foreground">
              AI-powered document chat
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} DocChat
          </span>
        </div>
      </footer>
    </div>
  );
}
