export const documents = [
  {
    id: "hr-policy",
    name: "인사규정.pdf",
    size: "1.8 MB",
    uploadedAt: "2026-05-04",
    uploadedTime: "오늘 09:12",
    pages: 24,
    chunks: 86,
    status: "처리 완료",
    progress: 100,
  },
  {
    id: "security-policy",
    name: "보안정책.pdf",
    size: "1.2 MB",
    uploadedAt: "2026-05-03",
    uploadedTime: "오늘 09:18",
    pages: 12,
    chunks: 41,
    status: "처리 완료",
    progress: 100,
  },
  {
    id: "onboarding-guide",
    name: "온보딩가이드.pdf",
    size: "860 KB",
    uploadedAt: "2026-05-02",
    uploadedTime: "오늘 09:21",
    pages: 18,
    chunks: 52,
    status: "처리 중",
    progress: 34,
  },
];

export const uploadQueue = [
  {
    ...documents[0],
    status: "처리 완료",
    progress: 100,
  },
  {
    ...documents[1],
    status: "임베딩 생성 중",
    progress: 75,
  },
  {
    id: "travel-expense",
    name: "출장비규정.pdf",
    size: "860 KB",
    uploadedAt: "2026-05-04",
    uploadedTime: "오늘 09:21",
    pages: 14,
    chunks: 38,
    status: "텍스트 추출 중",
    progress: 34,
  },
];

export const sources = [
  {
    id: "src-1",
    documentId: "hr-policy",
    documentName: "인사규정.pdf",
    page: 18,
    score: "0.92",
    text: "출산전후휴가는 90일로 하며, 출산 후 45일 이상을 보장한다...",
  },
  {
    id: "src-2",
    documentId: "hr-policy",
    documentName: "인사규정.pdf",
    page: 21,
    score: "0.88",
    text: "다태아 임신의 경우 출산전후휴가는 총 120일로 적용한다...",
  },
  {
    id: "src-3",
    documentId: "security-policy",
    documentName: "보안정책.pdf",
    page: 4,
    score: "0.61",
    text: "개인정보 및 민감정보 조회 시 접근 권한과 감사 로그를 확인한다...",
  },
];

export const pageSources = [
  {
    page: "17",
    title: "제6장 근태 관리",
    section: "제28조 근무시간",
    score: "0.74",
    highlight:
      "정규 근무시간은 회사가 정한 기준에 따르며, 부서별 업무 특성에 따라 조정될 수 있다.",
    chunk:
      "정규 근무시간은 회사가 정한 기준에 따르며, 부서별 업무 특성에 따라 조정될 수 있다. 근태 기록은 시스템에 의해 관리된다.",
    answer: "근무시간은 회사 기준에 따르며 부서별로 조정될 수 있습니다.",
  },
  {
    page: "18",
    title: "제7장 휴가 및 복무",
    section: "제32조 출산전후휴가",
    score: "0.92",
    highlight:
      "출산전후휴가는 총 90일로 하며, 출산 후 휴가 기간은 최소 45일 이상 확보되어야 한다.",
    chunk:
      "출산전후휴가는 총 90일로 하며, 출산 후 휴가 기간은 최소 45일 이상 확보되어야 한다. 다태아 임신의 경우 출산전후휴가는 총 120일로 한다.",
    answer: "출산전후휴가는 총 90일입니다.",
  },
  {
    page: "19",
    title: "제7장 휴가 및 복무",
    section: "제33조 육아휴직",
    score: "0.81",
    highlight:
      "육아휴직은 관련 법령과 회사 규정에 따라 신청할 수 있으며, 승인 절차를 거친다.",
    chunk:
      "육아휴직은 관련 법령과 회사 규정에 따라 신청할 수 있으며, 승인 절차를 거친다. 신청자는 사전에 필요 서류를 제출해야 한다.",
    answer: "육아휴직은 규정에 따라 신청 및 승인 절차를 거칩니다.",
  },
];