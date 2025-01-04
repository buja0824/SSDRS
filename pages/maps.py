import requests
import folium
from streamlit_folium import st_folium
import streamlit as st

# 병원 데이터 가져오기 (OpenStreetMap API 사용, 신경 키워드 필터 추가)
def get_hospitals(lat, lon, radius=5):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:{radius * 1000},{lat},{lon});
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    hospitals = []
    for element in data['elements']:
        if 'lat' in element and 'lon' in element:
            name = element.get("tags", {}).get("name", "")
            description = element.get("tags", {}).get("description", "")
            # "신경" 키워드 필터링
            if "신경" in name or "신경" in description:
                hospitals.append({
                    "name": name if name else "Unknown",
                    "lat": element['lat'],
                    "lon": element['lon']
                })
    return hospitals

# Streamlit 앱
def main():
    st.title("신경 관련 병원 찾기")
    st.markdown("**앱 실행 후 사용자의 현재 위치를 기반으로 병원을 검색합니다.**")

    # 세션 상태 초기화
    if "user_lat" not in st.session_state:
        st.session_state["user_lat"] = None
    if "user_lon" not in st.session_state:
        st.session_state["user_lon"] = None
    if "map_created" not in st.session_state:
        st.session_state["map_created"] = False

    # 사용자 위치 입력 (수동 모드)
    st.markdown("### 사용자의 위치는 다음과 같습니다:")
    user_lat = st.number_input("위도", value=37.765975, format="%.6f")
    user_lon = st.number_input("경도", value=126.77436, format="%.6f")

    # 위치 데이터 업데이트
    if user_lat and user_lon:
        st.session_state["user_lat"] = user_lat
        st.session_state["user_lon"] = user_lon

    # 반경 설정
    radius = st.slider("반경 (킬로미터)", min_value=1, max_value=20, value=5)

    # 지도 표시 및 병원 검색
    if st.session_state["user_lat"] and st.session_state["user_lon"]:
        st.success(f"현재 위치: ({st.session_state['user_lat']}, {st.session_state['user_lon']})")

        if not st.session_state["map_created"]:
            hospitals = get_hospitals(st.session_state["user_lat"], st.session_state["user_lon"], radius)

            if not hospitals:
                st.warning("반경 내 '신경' 관련 병원을 찾을 수 없습니다.")
            else:
                st.success(f"{len(hospitals)}개의 '신경' 관련 병원이 발견되었습니다!")

                # 지도 생성
                map_center = [st.session_state["user_lat"], st.session_state["user_lon"]]
                m = folium.Map(location=map_center, zoom_start=14)

                # 현재 위치 마커
                folium.Marker(location=map_center, popup="현재 위치", icon=folium.Icon(color="blue")).add_to(m)

                # 병원 마커 추가
                for hospital in hospitals:
                    folium.Marker(
                        location=[hospital['lat'], hospital['lon']],
                        popup=hospital['name'],
                        icon=folium.Icon(color="red", icon="plus")
                    ).add_to(m)

                # 지도를 세션 상태에 저장
                st.session_state["map_created"] = True
                st.session_state["map_object"] = m

    # 지도 출력
    if st.session_state["map_created"]:
        st_data = st_folium(st.session_state["map_object"], width=700, height=500)
    else:
        st.info("위치를 입력한 후 병원을 검색하세요.")

if __name__ == "__main__":
    main()