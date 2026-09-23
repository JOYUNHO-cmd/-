# Vercel 연결 안내

1. Vercel에서 Add New → Project로 이 GitHub 저장소를 Import합니다.
2. Root Directory는 저장소 루트로 둡니다. vercel.json에 Framework Other, 빌드 없음, 출력 dist가 설정되어 있습니다.
3. Deploy를 실행합니다. 이미 생성된 787개 정적 페이지를 배포합니다.

## 회사 정보 수정

brand.json을 수정하고 Python 3.9 이상으로 아래 명령을 실행한 후 변경된 파일과 dist를 함께 커밋합니다.

```sh
python scripts/build.py
```

Vercel에서는 Python 빌드를 실행하지 않고 커밋된 dist를 사용합니다.
최종 도메인이 정해지면 brand.json의 origin을 해당 HTTPS 주소로 바꾸고 다시 빌드하세요. 현재는 기존 비공개 검토 주소가 canonical과 사이트맵에 설정되어 있습니다.

## 공개 여부 주의

현재 private_preview는 true로 검색 색인을 차단하지만, 이는 로그인이나 접근 보호 기능이 아닙니다. 기존 Sites의 비공개 접근 제어는 Vercel로 이전되지 않습니다. 비공개로 검토하려면 배포 전에 Vercel의 Deployment Protection을 별도로 설정하세요.

실제 공개할 때에는 회사 정보와 전화번호, origin을 채우고 private_preview를 false로 바꿔 다시 빌드합니다.
원본 README는 보존했고 사이트 설명은 SITE-README.md에 있습니다.
