class HRTools:
    
    @staticmethod
    def get_brand_kpi(brand_name: str):
        db = {
            "gucci": {"talent_mobility": "15%", "leadership_score": 4.2},
            "saint_laurent": {"talent_mobility": "10%", "leadership_score": 3.8}
        }
        return db.get(brand_name.lower(), "Không tìm thấy")

    @staticmethod
    def check_nda_status(employee_id: str):
        return "Active - Confidentiality Agreement Signed"