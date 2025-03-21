import os
import re
import glob
import json
import argparse
from markdownify import markdownify as markdown

from utils.Classes import GraphState, LayoutAnalyzer
from utils.funcs import *
from utils.extracts import *
from utils.crops import *
from utils.creates import *
from utils.save import save_results
from utils.vectordb import build_db
from utils.prompt import summary_prompt, map_prompt, trans_prompt

from dotenv import load_dotenv
load_dotenv()

# DB 업데이트 함수: Paper 모델의 상태와 분석 결과 업데이트
def update_paper_status(paper_id: int, original_content: str, english_summary: str, translation: str, korean_summary: str):
    from database import SessionLocal
    from models import models
    db = SessionLocal()
    try:
        paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
        if paper:
            paper.processing_status = "completed"
            paper.original_content = original_content
            paper.english_summary = english_summary
            paper.translation = translation
            paper.korean_summary = korean_summary
            db.commit()
            print(f"Paper id {paper_id} 상태가 'completed'로 업데이트되었습니다.")
        else:
            print(f"Paper record with id {paper_id} not found.")
    except Exception as e:
        db.rollback()
        print(f"Error updating paper status: {e}")
    finally:
        db.close()


def split_and_update(state):
    """PDF 파일을 분할하고 상태를 업데이트"""
    split_file_list = split_pdf(state)
    state.update(split_file_list)
    return state


def paper_analysis(analyzer, state):
    """논문 레이아웃 분석 및 요소 추출"""
    # 레이아웃 분석
    state_out = analyze_layout(analyzer, state)
    state.update(state_out)
    
    # 메타데이터 및 요소 추출
    state_out = extract_page_metadata(state)
    state.update(state_out)
    
    state_out = extract_page_elements(state)
    state.update(state_out)
    
    state_out = extract_tag_elements_per_page(state)
    state.update(state_out)
    
    state_out = page_numbers(state)
    state.update(state_out)
    
    # 이미지, 테이블, 수식 추출
    state_out = crop_image(state)
    state.update(state_out)
    
    state_out = crop_table(state)
    state.update(state_out)

    state_out = crop_equation(state)
    state.update(state_out)

    # 텍스트 추출
    state_out = extract_page_text(state)
    state.update(state_out)
    
    return state


def generate_summaries(state, text_summary_chain, paper_summary_chain, trans_chain):
    """요약 및 번역 생성"""
    # 텍스트 요약 생성
    state_out = create_text_summary(text_summary_chain, state)
    state.update(state_out)

    state_out = map_reduce_summary(paper_summary_chain, state)
    state.update(state_out)

    # 요약 번역
    state_out = create_text_trans_summary(trans_chain, state)
    state.update(state_out)

    # 이미지 요약 생성
    state_out = create_image_summary_data_batches(state)
    state.update(state_out)

    state_out = create_image_summary(state)
    state.update(state_out)

    # 테이블 요약 생성
    state_out = create_table_summary_data_batches(state)
    state.update(state_out)

    state_out = create_table_summary(state)
    state.update(state_out)

    # 수식 요약 생성
    state_out = create_equation_summary_data_batches(state)
    state.update(state_out)

    state_out = create_equation_summary(state)
    state.update(state_out)

    # 테이블 마크다운 생성
    state_out = create_table_markdown(state)
    state.update(state_out)

    return state


def save_analysis_results(state, output_folder, filename):
    """분석 결과 저장"""
    # 수식 이미지 처리: HTML 콘텐츠 내 적절한 위치에 수식 결과 삽입
    cnt = 1
    for key, value in state['equation_summary'].items():
        equation_html = f"<p id='{key}_1' data-category='equation' style='font-size:14px'>{value}</p>"
        state['html_content'].insert(cnt + int(key), equation_html)
        cnt += 1

    # 생성 내용 저장 (HTML → Markdown 변환)
    md_output_file = save_results(output_folder, filename, state['html_content'])
    print(f"기본 마크다운 파일: {md_output_file}")
    
    # 분석결과 JSON 저장
    output_file = f"{output_folder}/{filename}_analy.json"
    with open(output_file, "w", encoding='utf-8') as file:
        json.dump(state, file, ensure_ascii=False)
    print(f"분석 결과 JSON 파일: {output_file}")

    # 임시 파일 제거
    for del_file in state['split_filepaths'] + state['analyzed_files']:
        os.remove(del_file)
        
    return output_file


def create_translated_markdown(trans_chain, output_folder, filename):
    """통번역 결과 마크다운 생성"""
    original_paper_md = f"{output_folder}/{filename}.md"
    new_docs = load_and_split(original_paper_md)
    translated_paragraph = ['# ' + new_docs[0].metadata['Header 1']] + trans_chain.batch(new_docs[1:])
    combined_content = "\n".join(translated_paragraph)
    md_output = markdown(combined_content)

    trans_paper_md = f"{output_folder}/{filename}_trans.md"
    with open(trans_paper_md, "w", encoding="utf-8") as f:
        f.write(md_output)

    print(f"번역된 마크다운 파일: {trans_paper_md}")
    return trans_paper_md


def create_english_summary(output_file, output_folder, filename):
    """영어 요약 마크다운 생성"""
    with open(output_file, "r", encoding='utf-8') as f:
        json_data = json.load(f)
        
    markdown_contents = []
    
    names = json_data['section_names']
    for i, page in enumerate(json_data['texts_summary'].keys()):
        page = int(page)
        if names[page] == 'References':
            continue
            
        text_summary = json_data['texts_summary'][str(page)]
        section_title = f'# {names[page]}'
        if i == 0:
            text_summary = json_data['paper_summary']
        
        markdown_contents.append(section_title)
        markdown_contents.append(text_summary)
        
        # 이미지 추가
        for image_data in json_data['image_summary_data_batches']:
            if image_data['page'] == page:
                img_file = image_data['image'] # .split('/')[-1]
                img_name = os.path.basename(img_file).split('.')[-1]
                markdown_contents.append(f'\n ![{img_name}]({img_file}) \n')
                
        # 테이블 추가
        for table_data in json_data['table_summary_data_batches']:
            if table_data['page'] == page:
                table_img_file = table_data['table'] # .split('/')[-1]
                table_img_name = os.path.basename(table_img_file).split('.')[-1]
                markdown_contents.append(f'\n ![{table_img_name}]({table_img_file}) \n')

    markdown_file_path = f'{output_folder}/{filename}_summary_en.md'
    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_contents))
    
    print(f"영어 요약 마크다운 파일: {markdown_file_path}")
    return markdown_file_path


def create_korean_summary(output_file, output_folder, filename):
    """한국어 요약 마크다운 생성"""
    with open(output_file, "r", encoding='utf-8') as f:
        json_data = json.load(f)
        
    markdown_contents = []
    names = json_data['section_names']
    
    for i, page in enumerate(json_data['texts_summary'].keys()):
        page = int(page)
        if names[page] == 'References':
            continue
            
        if i == 0:
            text_summary = json_data['paper_trans_summary']
        else:
            text_summary = json_data['texts_trans_summary'][str(page)]
            
        section_title = f'# {names[page]}'
        
        markdown_contents.append(section_title)
        markdown_contents.append(text_summary)
        
        # 이미지 추가
        for image_data in json_data['image_summary_data_batches']:
            if image_data['page'] == page:
                img_file = image_data['image'] # .split('/')[-1]
                img_name = os.path.basename(img_file).split('.')[-1]
                markdown_contents.append(f'![{img_name}]({img_file})')
        
        # 테이블 추가        
        for table_data in json_data['table_summary_data_batches']:
            if table_data['page'] == page:
                table_img_file = table_data['table'] # .split('/')[-1]
                table_img_name = os.path.basename(table_img_file).split('.')[-1]
                markdown_contents.append(f'![{table_img_name}]({table_img_file})')

    markdown_file_path = f'{output_folder}/{filename}_summary_ko.md'
    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_contents))
    
    print(f"한국어 요약 마크다운 파일: {markdown_file_path}")
    return markdown_file_path


def main(args):
    # 인자에서 PDF 파일 경로, 모델 이름, API 키 받아오기
    file_path = args.file_path
    selected_model = args.model
    openai_api_key = args.openai_api
    upstage_api_key = args.upstage_api
    paper_id = args.paper_id
    
    if not openai_api_key:
        raise ValueError("사용자 OpenAI API key가 필요합니다.")
    if not upstage_api_key:
        raise ValueError("사용자 Upstage API key가 필요합니다.")

    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["UPSTAGE_API_KEY"] = upstage_api_key
    
    # Upstage API key를 사용하여 레이아웃 분석기 초기화
    analyzer = LayoutAnalyzer(upstage_api_key)
    
    llm = ChatOpenAI(
        model_name=selected_model,
        temperature=0,
        api_key=openai_api_key
    )
    
    # get_chain과 get_translator 함수는 사용자의 OpenAI API key를 활용하도록 수정되어야 합니다.
    # 아래 함수 호출 시 openai_api_key 인자를 추가로 전달합니다.
    text_summary_chain = get_chain(llm, summary_prompt)
    paper_summary_chain = get_chain(llm, map_prompt)
    trans_chain = get_translator(llm, trans_prompt)
    
    # 상태 초기화: PDF 파일 경로와 배치 크기 설정
    state = GraphState(filepath=file_path, batch_size=10)
    
    # 1. PDF 분할
    state = split_and_update(state)
    
    # 2. 논문 분석
    state = paper_analysis(analyzer, state)
    
    # 결과 파일 저장을 위한 출력 폴더 및 파일명 설정
    pdf_file = state["filepath"]
    output_folder = os.path.splitext(pdf_file)[0]
    filename = os.path.basename(pdf_file).split('.')[0]
    
    # 기본 분석 결과로 원본 마크다운 파일 생성
    md_output_file1 = save_results(output_folder, filename, state['html_content'])
    print(f"기본 마크다운 파일: {md_output_file1}")
    
    # 3. 요약 및 번역 생성
    state = generate_summaries(state, text_summary_chain, paper_summary_chain, trans_chain)
    
    # 4. 분석 결과 저장 (JSON 파일 생성 및 임시 파일 제거)
    output_file = save_analysis_results(state, output_folder, filename)
    
    # 5. 마크다운 결과물 생성
    trans_paper_md = create_translated_markdown(trans_chain, output_folder, filename)
    en_summary_md = create_english_summary(output_file, output_folder, filename)
    ko_summary_md = create_korean_summary(output_file, output_folder, filename)
    
    print("모든 분석 및 요약 작업이 완료되었습니다.")
    
    with open(md_output_file1, "r", encoding="utf-8") as f:
        original_content = f.read()
    with open(en_summary_md, "r", encoding="utf-8") as f:
        english_summary = f.read()
    with open(trans_paper_md, "r", encoding="utf-8") as f:
        translation = f.read()
    with open(ko_summary_md, "r", encoding="utf-8") as f:
        korean_summary = f.read()
    
    update_paper_status(paper_id, original_content, english_summary, translation, korean_summary)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='논문 분석 및 요약 생성')
    parser.add_argument(
        '--file_path',
        type=str,
        required=True,
        help='분석할 PDF 파일 경로'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini',
        help='사용할 AI 모델 (기본값: gpt-4o-mini)'
    )
    parser.add_argument(
        '--openai_api',
        type=str,
        required=True,
        help='사용자 OpenAI API key'
    )
    parser.add_argument(
        '--upstage_api',
        type=str,
        required=True,
        help='사용자 Upstage API key'
    )
    
    parser.add_argument(
        '--paper_id',
        type=int,
        required=True,
        help='업데이트할 Paper 모델의 ID'
    )

    args = parser.parse_args()
    main(args)
