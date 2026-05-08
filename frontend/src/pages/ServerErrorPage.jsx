import { useNavigate } from "react-router-dom";

import { AppLayout, PageShell } from "../components/ui";
import ErrorStateCard from "../components/ErrorStateCard";

export default function ServerErrorPage() {
  const navigate = useNavigate();

  return (
    <AppLayout>
      <PageShell className="items-center justify-center">
        <ErrorStateCard
          type="server-error"
          title="요청을 처리하지 못했습니다"
          description="일시적인 오류로 답변을 생성하지 못했습니다. 잠시 후 다시 시도하거나 문서 처리 상태를 확인해주세요."
          tips={[
            "잠시 후 다시 시도해보세요",
            "문서 처리 상태가 완료되었는지 확인하세요",
            "문제가 계속되면 문서를 다시 업로드해보세요",
          ]}
          primaryAction="다시 시도"
          secondaryAction="문서 다시 업로드"
          onPrimaryClick={() => navigate("/chat")}
          onSecondaryClick={() => navigate("/upload")}
        />
      </PageShell>
    </AppLayout>
  );
}
