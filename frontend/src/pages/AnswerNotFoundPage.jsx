import { useNavigate } from "react-router-dom";

import { AppLayout } from "../components/ui";
import ErrorStateCard from "../components/ErrorStateCard";

export default function AnswerNotFoundPage() {
  const navigate = useNavigate();

  return (
    <AppLayout>
      <div className="mx-auto flex min-h-[calc(100vh-136px)] max-w-[1200px] flex-col items-center justify-center">
        <ErrorStateCard
          type="not-found"
          title="문서에서 답을 찾을 수 없습니다"
          description="업로드된 문서에서 질문과 관련된 내용을 찾지 못했습니다. 질문을 더 구체적으로 입력하거나 관련 문서를 추가해보세요."
          tips={[
            "질문 표현을 바꿔보세요",
            "관련 문서가 업로드되어 있는지 확인하세요",
            "문서명이나 제도명을 함께 입력해보세요",
          ]}
          primaryAction="다시 질문하기"
          secondaryAction="다른 문서 선택"
          onPrimaryClick={() => navigate("/chat")}
          onSecondaryClick={() => navigate("/documents")}
        />
      </div>
    </AppLayout>
  );
}