---
name: 카카오 REST API 키
description: 사용자의 카카오 REST API 키 (지오코딩 등 카카오 API 사용 시 참조)
type: reference
---

카카오 REST API 키: 사용자 PC `.env` 파일 또는 별도 secret 저장소에서 로드 (코드·문서에 평문 저장 금지)

- 용도: 카카오맵 지오코딩, 키워드 검색 등
- 헤더: `Authorization: KakaoAK {키}`
- 일 30만건 무료 한도
- **보안 주의**: 코드 외부 노출 금지, 로그·스크린샷 등에 포함되지 않도록 주의
