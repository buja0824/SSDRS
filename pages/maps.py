import requests
import folium
from streamlit_folium import st_folium
import streamlit as st

# 병원 데이터 가져오기 (OpenStreetMap API 사용)
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
            name = element.get("tags", {}).get("name", "Unknown")
            # General hospital ("General Hospital") condition filtering
            if "General Hospital" in name:
                hospitals.append({
                    "name": name,
                    "lat": element['lat'],
                    "lon": element['lon']
                })
    return hospitals

# 주요 병원 데이터
major_hospitals = [
    {"name": "Bệnh viện Bạch Mai (박마이 병원)", "lat": 21.003174, "lon": 105.841674},
    {"name": "Bệnh viện Hữu Nghị Việt Đức (비엣덕 병원)", "lat": 21.027781, "lon": 105.846313},
    {"name": "Bệnh viện Chợ Rẫy (초레이 병원)", "lat": 10.762622, "lon": 106.660172},
    {"name": "Bệnh viện Nhân Dân 115 (인민 115 병원)", "lat": 10.767236, "lon": 106.667561},
    {"name": "Bệnh viện Đà Nẵng (다낭 병원)", "lat": 16.067971, "lon": 108.207161},
    {"name": "Bệnh viện C Đà Nẵng (다낭 C 병원)", "lat": 16.068768, "lon": 108.213500},
    {"name": "Vinmec International Hospital (빈멕 국제 병원)", "lat": 20.999540, "lon": 105.810394}
]

# Streamlit 앱
def main():
    st.title("Finding All Hospitals")
    st.markdown("**After running the web, it finds all hospitals based on the user's current location.**")

    # 세션 상태 초기화
    if "user_lat" not in st.session_state:
        st.session_state["user_lat"] = None
    if "user_lon" not in st.session_state:
        st.session_state["user_lon"] = None
    if "map_created" not in st.session_state:
        st.session_state["map_created"] = False

    # 사용자 위치 입력 (수동 모드)
    st.markdown("### The user's location is as follows:")
    user_lat = st.number_input("Latitude", value=16.0439678, format="%.6f")
    user_lon = st.number_input("Longitude", value=108.1993461, format="%.6f")

    # 위치 데이터 업데이트
    if user_lat and user_lon:
        st.session_state["user_lat"] = user_lat
        st.session_state["user_lon"] = user_lon

    # 반경 설정
    radius = st.slider("Radius (in kilometers)", min_value=1, max_value=100, value=5)

    # 병원 검색 및 지도 업데이트
    if st.button("Search Hospitals"):
        if st.session_state["user_lat"] and st.session_state["user_lon"]:
            st.success(f"Current Location: ({st.session_state['user_lat']}, {st.session_state['user_lon']})")

            hospitals = get_hospitals(st.session_state["user_lat"], st.session_state["user_lon"], radius)

            if not hospitals:
                st.warning("No hospitals found within the specified radius.")
                st.session_state["map_created"] = False
            else:
                st.success(f"{len(hospitals)} general hospitals have been found!")

                # 지도 생성
                map_center = [st.session_state["user_lat"], st.session_state["user_lon"]]
                m = folium.Map(location=map_center, zoom_start=14)

                # 현재 위치 마커
                folium.Marker(location=map_center, popup="Current Location", icon=folium.Icon(color="blue")).add_to(m)

                # 병원 마커 추가
                for hospital in hospitals:
                    folium.Marker(
                        location=[hospital['lat'], hospital['lon']],
                        popup=hospital['name'],
                        icon=folium.Icon(color="red", icon="plus")
                    ).add_to(m)

                # 주요 병원 마커 추가
                for major_hospital in major_hospitals:
                    folium.Marker(
                        location=[major_hospital['lat'], major_hospital['lon']],
                        popup=major_hospital['name'],
                        icon=folium.Icon(color="green", icon="star")
                    ).add_to(m)

                # 지도를 세션 상태에 저장
                st.session_state["map_created"] = True
                st.session_state["map_object"] = m

    # 지도 출력
    if st.session_state.get("map_created"):
        st_folium(st.session_state["map_object"], width=700, height=500)
    else:
        st.info("Enter a location and search for hospitals.")

if __name__ == "__main__":
    main()
