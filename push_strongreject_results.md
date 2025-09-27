# StrongReject 결과 Push 가이드

## 1. 서버에서 작업 확인
```bash
# 현재 실행 중인 tmux 세션 확인
tmux ls

# 세션 attach해서 진행상황 확인 (예: session 0)
tmux attach -t 0

# 세션에서 나오기 (detach): Ctrl+B, then D
```

## 2. 결과 파일 확인
```bash
# evaluation_results 디렉토리 확인
ls -la evaluation_results/

# 16개 기존 언어 평가 결과 확인
ls -la evaluation_results/*_evaluated.json | wc -l
# 16개 파일이 있어야 함

# 새로운 24개 언어 결과 확인 (있다면)
ls -la evaluation_results/*_results.json | wc -l
```

## 3. Git으로 Push하기

### Option A: 모든 결과 한번에 push
```bash
# 현재 상태 확인
git status

# 모든 evaluation 결과 추가
git add evaluation_results/*.json

# 커밋
git commit -m "Add StrongReject evaluation results for 16 languages"

# Push
git push origin main
```

### Option B: 단계별로 push
```bash
# 1. 16개 기존 언어 결과만 먼저
git add evaluation_results/*_evaluated.json
git commit -m "Add entry-level StrongReject evaluation for 16 existing languages"
git push

# 2. 나중에 24개 새 언어 결과 (완료되면)
git add evaluation_results/*_results.json
git commit -m "Add StrongReject evaluation for 24 new languages"
git push

# 3. Summary 파일들
git add evaluation_results/*_summary.json evaluation_results/*_report.*
git commit -m "Add evaluation summary reports"
git push
```

## 4. 대용량 파일 처리 (필요한 경우)
```bash
# 파일 크기 확인
du -h evaluation_results/*.json

# 만약 파일이 100MB 이상이면 Git LFS 사용
git lfs track "evaluation_results/*.json"
git add .gitattributes
git add evaluation_results/*.json
git commit -m "Add large evaluation results with LFS"
git push
```

## 5. 충돌 해결 (필요시)
```bash
# 만약 push 실패하면
git pull --rebase origin main

# 충돌 있으면 해결 후
git add .
git rebase --continue

# 다시 push
git push origin main
```

## 체크리스트
- [ ] `evaluation_results/` 디렉토리 생성됨
- [ ] 16개 언어 `*_evaluated.json` 파일 있음
- [ ] 각 파일에 entry별 evaluation 점수 있음
- [ ] base_prompt, num_turns 등 metadata 포함됨
- [ ] Summary 파일 생성됨

## 파일 구조 예시
```
evaluation_results/
├── rus.Cyrl_evaluated.json
├── cmn.Hani_evaluated.json
├── deu.Latn_evaluated.json
├── spa.Latn_evaluated.json
├── jpn.Jpan_evaluated.json
├── fra.Latn_evaluated.json
├── ita.Latn_evaluated.json
├── por.Latn_evaluated.json
├── pol.Latn_evaluated.json
├── nld.Latn_evaluated.json
├── ind.Latn_evaluated.json
├── tur.Latn_evaluated.json
├── ces.Latn_evaluated.json
├── kor.Hang_evaluated.json
├── arb.Arab_evaluated.json
├── ron.Latn_evaluated.json
└── existing_16_languages_summary.json
```