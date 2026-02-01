import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useDocumentUpload } from '@/hooks/useUpload';
import { useChatStore } from '@/stores/chatStore';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export const DocumentUpload = () => {
  const { mutate: uploadDocument, isPending, isSuccess, isError, data, uploadProgress } = useDocumentUpload();
  const setCurrentDoc = useChatStore((state) => state.setCurrentDoc);
  const addUploadedDocument = useChatStore((state) => state.addUploadedDocument);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        uploadDocument(file, {
          onSuccess: (response) => {
            setCurrentDoc(response.doc_id);
            addUploadedDocument({
              doc_id: response.doc_id,
              filename: file.name,
              pages: response.pages,
              uploadedAt: new Date().toISOString(),
            });
          },
        });
      }
    },
    [uploadDocument, setCurrentDoc, addUploadedDocument]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    maxFiles: 1,
    disabled: isPending,
  });

  return (
    <Card className="w-full border-2 transition-all duration-200 hover:shadow-lg">
      <CardContent className="p-0">
        <div
          {...getRootProps()}
          className={`
            relative p-12 text-center cursor-pointer transition-all duration-300
            ${isDragActive ? 'bg-primary/5 border-primary' : 'hover:bg-accent/50'}
            ${isPending ? 'opacity-70 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />

          <div className="flex flex-col items-center gap-6">
            {isPending ? (
              <>
                <div className="relative">
                  <Loader2 className="w-16 h-16 text-primary animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Upload className="w-8 h-8 text-primary/50" />
                  </div>
                </div>
                <div className="w-full max-w-md space-y-3">
                  <Progress value={uploadProgress} className="h-2" />
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Processing document...</span>
                    <span className="font-medium text-primary">{uploadProgress}%</span>
                  </div>
                </div>
              </>
            ) : isSuccess && data ? (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-green-500/10 rounded-full animate-ping" />
                  <CheckCircle2 className="relative w-16 h-16 text-green-500" />
                </div>
                <div className="space-y-4 w-full">
                  <div className="flex items-center justify-center gap-2">
                    <FileText className="w-5 h-5 text-green-600" />
                    <span className="text-lg font-semibold text-green-700">Upload Successful!</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 max-w-lg mx-auto">
                    <div className="bg-accent/50 rounded-lg p-3">
                      <div className="text-xs text-muted-foreground">Pages</div>
                      <div className="text-2xl font-bold text-foreground">{data.pages}</div>
                    </div>
                    <div className="bg-accent/50 rounded-lg p-3">
                      <div className="text-xs text-muted-foreground">Vectors</div>
                      <div className="text-2xl font-bold text-foreground">{data.upserted_vectors}</div>
                    </div>
                    <div className="bg-accent/50 rounded-lg p-3">
                      <div className="text-xs text-muted-foreground">Chunks</div>
                      <div className="text-2xl font-bold text-foreground">
                        {data.parent_chunks + data.child_chunks}
                      </div>
                    </div>
                    <div className="bg-accent/50 rounded-lg p-3">
                      <div className="text-xs text-muted-foreground">Images</div>
                      <div className="text-2xl font-bold text-foreground">{data.images}</div>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs font-mono">
                    ID: {data.doc_id.slice(0, 8)}...
                  </Badge>
                </div>
              </>
            ) : isError ? (
              <>
                <XCircle className="w-16 h-16 text-destructive" />
                <div className="space-y-2">
                  <p className="text-lg font-semibold text-destructive">Upload Failed</p>
                  <p className="text-sm text-muted-foreground">Please try again with a different file</p>
                </div>
              </>
            ) : (
              <>
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/5 rounded-full blur-xl" />
                  <Upload className="relative w-16 h-16 text-primary" />
                </div>
                <div className="space-y-3">
                  <h3 className="text-2xl font-semibold text-foreground">
                    {isDragActive ? 'Drop your file here' : 'Upload Document'}
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Drag & drop your document here, or click to browse
                  </p>
                  <div className="flex gap-2 justify-center flex-wrap">
                    <Badge variant="outline" className="text-xs">
                      PDF
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      DOCX
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      Images
                    </Badge>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
