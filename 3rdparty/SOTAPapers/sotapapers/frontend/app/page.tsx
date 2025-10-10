'use client';

import { trpc } from '../lib/trpc';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

// Enums if needed, based on backend PaperType, PaperSessionType, PaperAcceptStatus etc.

interface PaperContent {
  abstract?: string | null;
  references: string[]; // Backend maps to List[Paper], but we get IDs as strings
  cited_by: string[];   // Backend maps to List[Paper], but we get IDs as strings
  bibtex?: string | null;
  primary_task?: string | null;
  secondary_task?: string | null;
  tertiary_task?: string | null;
  primary_method?: string | null;
  secondary_method?: string | null;
  tertiary_method?: string | null;
  datasets_used?: string[];
  metrics_used?: string[];
  comparisons?: Record<string, any>; // Assuming a dictionary for now
  limitations?: string | null;
}

interface PaperMedia {
  pdf_url?: string | null;
  youtube_url?: string | null;
  github_url?: string | null;
  project_page_url?: string | null;
  arxiv_url?: string | null;
}

interface PaperMetrics {
  github_star_count?: number | null;
  github_star_avg_hype?: number | null;
  github_star_weekly_hype?: number | null;
  github_star_monthly_hype?: number | null;
  github_star_tracking_start_date?: string | null;
  github_star_tracking_latest_footprint?: Record<string, number>; // Assuming a dictionary for now
  citations_total?: number | null;
}

interface Paper {
  id: string;
  arxiv_id?: string | null;
  title: string;
  authors: string[]; // Corrected to string[] based on backend schema
  affiliations?: string[] | null;
  affiliations_country?: string[] | null;
  year?: number | null;
  venue?: string | null;
  pages?: string[] | null;
  paper_type?: string | null; // Using string for enum for simplicity
  session_type?: string | null; // Using string for enum for simplicity
  accept_status?: string | null; // Using string for enum for simplicity
  note?: string | null;
  content?: PaperContent | null;
  media?: PaperMedia | null;
  metrics?: PaperMetrics | null;
}

export default function TopPapers() {
  const { data: papers, isLoading } = trpc.papers.top.useQuery({ limit: 10 });

  return (
    <Card className="max-w-4xl mx-auto my-8">
      <CardHeader>
        <CardTitle>Top Papers by Hype Score</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Authors</TableHead>
                  <TableHead>Hype Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {papers?.map((paper: Paper) => (
                  <TableRow key={paper.id}>
                    <TableCell className="font-medium text-blue-600 hover:underline cursor-pointer">{paper.title}</TableCell>
                    <TableCell>{paper.authors.join(', ')}</TableCell>
                    <TableCell>{paper.metrics?.github_star_avg_hype}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
